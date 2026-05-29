# PHP Examples

Examples using Laravel (primary) and Symfony (secondary).

## Route Definition and URL Structure

```php
// routes/api.php — Laravel
use Illuminate\Support\Facades\Route;
use App\Http\Controllers\OrderController;

Route::prefix('v1')->middleware('auth:sanctum')->group(function () {
    // Collection and resource routes
    Route::get('orders',          [OrderController::class, 'index']);
    Route::post('orders',         [OrderController::class, 'store']);
    Route::get('orders/{id}',     [OrderController::class, 'show']);
    Route::patch('orders/{id}',   [OrderController::class, 'update']);
    Route::delete('orders/{id}',  [OrderController::class, 'destroy']);

    // Sub-collection
    Route::get('orders/{id}/items', [OrderController::class, 'items']);

    // Task-based URLs — domain operations
    Route::post('orders/{id}/cancel', [OrderController::class, 'cancel']);
    Route::post('orders/{id}/ship',   [OrderController::class, 'ship']);
});


// Symfony — config/routes.yaml
// Or via annotations/attributes in the controller:
#[Route('/v1/orders', name: 'orders_')]
class OrderController extends AbstractController
{
    #[Route('', name: 'list',   methods: ['GET'])]
    #[Route('', name: 'create', methods: ['POST'])]
    #[Route('/{id}', name: 'show',   methods: ['GET'])]
    #[Route('/{id}', name: 'update', methods: ['PATCH'])]
    #[Route('/{id}', name: 'delete', methods: ['DELETE'])]
    #[Route('/{id}/cancel', name: 'cancel', methods: ['POST'])]
}
```

## Status Codes in Responses

```php
// Laravel — using response helpers
class OrderController extends Controller
{
    public function store(CreateOrderRequest $request): JsonResponse
    {
        $order = $this->orderService->create($request->validated());

        return response()->json($order->toArray(), 201)
            ->header('Location', "/v1/orders/{$order->id}");
    }

    public function destroy(string $id): JsonResponse
    {
        $this->orderService->delete($id);
        return response()->noContent(); // 204
    }

    public function cancel(string $id): JsonResponse
    {
        $order = $this->orderService->cancel($id, auth()->id());
        return response()->json($order->toArray(), 200);
    }
}
```

## Request Validation

```php
// Laravel Form Request — validation runs before the controller method
namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class CreateOrderRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'customer_id'              => ['required', 'uuid'],
            'items'                    => ['required', 'array', 'min:1'],
            'items.*.product_id'       => ['required', 'uuid'],
            'items.*.quantity'         => ['required', 'integer', 'min:1'],
            'shipping_address.street'  => ['required', 'string'],
            'shipping_address.city'    => ['required', 'string'],
            'shipping_address.postal_code' => ['required', 'string'],
            'shipping_address.country' => ['required', 'string', 'size:2'],
        ];
    }
}

// Laravel returns 422 automatically with all errors when validation fails:
// {
//   "message": "The given data was invalid.",
//   "errors": {
//     "items": ["The items field must contain at least 1 items."],
//     "shipping_address.country": ["The shipping address.country must be 2 characters."]
//   }
// }

// To use RFC 7807 format, override failedValidation:
protected function failedValidation(Validator $validator)
{
    $errors = collect($validator->errors()->toArray())
        ->map(fn ($messages, $field) => ['field' => $field, 'message' => $messages[0]])
        ->values()
        ->all();

    throw new HttpResponseException(response()->json([
        'type'   => 'https://api.example.com/errors/validation-failed',
        'title'  => 'Validation Failed',
        'status' => 422,
        'detail' => 'The request body contains fields that failed validation.',
        'errors' => $errors,
    ], 422));
}
```

## Error Response Format (RFC 7807)

```php
// app/Exceptions/Handler.php — Laravel
namespace App\Exceptions;

use Illuminate\Foundation\Exceptions\Handler as ExceptionHandler;
use Symfony\Component\HttpFoundation\Response;

class Handler extends ExceptionHandler
{
    public function render($request, Throwable $e): Response
    {
        if ($request->expectsJson()) {
            return $this->handleApiException($request, $e);
        }
        return parent::render($request, $e);
    }

    private function handleApiException($request, Throwable $e): JsonResponse
    {
        if ($e instanceof OrderNotFoundException) {
            return $this->problem(404, 'ORDER_NOT_FOUND', $e->getMessage());
        }
        if ($e instanceof OrderAlreadyCancelledException) {
            return $this->problem(409, 'ORDER_ALREADY_CANCELLED', 'This order has already been cancelled.');
        }
        if ($e instanceof InsufficientStockException) {
            return $this->problem(422, 'INSUFFICIENT_STOCK', "Stock is short by {$e->shortfall} units.");
        }

        logger()->error('Unhandled exception', ['exception' => $e]);
        return $this->problem(500, 'INTERNAL_ERROR', 'An unexpected error occurred.');
    }

    private function problem(int $status, string $code, string $detail): JsonResponse
    {
        $slug = strtolower(str_replace('_', '-', $code));
        return response()->json([
            'type'   => "https://api.example.com/errors/{$slug}",
            'title'  => str_replace('_', ' ', $code),
            'status' => $status,
            'detail' => $detail,
        ], $status);
    }
}
```

## Pagination

```php
// Laravel built-in pagination
class OrderController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $perPage = min($request->integer('per_page', 25), 100);

        $paginator = Order::query()
            ->when($request->status, fn ($q, $v) => $q->where('status', $v))
            ->orderBy($request->get('sort', 'created_at'), $request->get('order', 'desc'))
            ->paginate($perPage);

        // Build Link header
        $links = [];
        if ($paginator->onFirstPage() === false) {
            $links[] = "<{$paginator->previousPageUrl()}>; rel=\"prev\"";
        }
        if ($paginator->hasMorePages()) {
            $links[] = "<{$paginator->nextPageUrl()}>; rel=\"next\"";
        }
        $links[] = "<{$paginator->url(1)}>; rel=\"first\"";
        $links[] = "<{$paginator->url($paginator->lastPage())}>; rel=\"last\"";

        return response()->json([
            'data' => $paginator->items(),
            'meta' => [
                'total'    => $paginator->total(),
                'page'     => $paginator->currentPage(),
                'per_page' => $paginator->perPage(),
            ],
        ])->header('Link', implode(', ', $links))
          ->header('X-Total-Count', $paginator->total());
    }
}
```

## Filtering and Sorting

```php
class OrderController extends Controller
{
    public function index(Request $request): JsonResponse
    {
        $request->validate([
            'status'      => ['nullable', 'in:pending,confirmed,shipped,cancelled'],
            'customer_id' => ['nullable', 'uuid'],
            'sort'        => ['nullable', 'in:created_at,total,status'],
            'order'       => ['nullable', 'in:asc,desc'],
        ]);

        $orders = Order::query()
            ->when($request->status,      fn ($q, $v) => $q->where('status', $v))
            ->when($request->customer_id, fn ($q, $v) => $q->where('customer_id', $v))
            ->orderBy($request->get('sort', 'created_at'), $request->get('order', 'desc'))
            ->paginate(min($request->integer('per_page', 25), 100));

        return response()->json($orders);
    }
}
```

## Authentication Middleware (Sanctum / JWT)

```php
// Laravel Sanctum — stateless API tokens
// routes/api.php
Route::middleware('auth:sanctum')->group(function () {
    Route::get('orders', [OrderController::class, 'index']);
});

// Controller — access authenticated user
public function store(CreateOrderRequest $request): JsonResponse
{
    $user = $request->user(); // injected by Sanctum
    $order = $this->orderService->create($request->validated(), $user->id);
    ...
}

// Return 401 when unauthenticated — override in app/Exceptions/Handler.php:
protected function unauthenticated($request, AuthenticationException $exception)
{
    return response()->json([
        'type'   => 'https://api.example.com/errors/unauthorized',
        'title'  => 'Unauthorized',
        'status' => 401,
        'detail' => 'Authentication is required to access this resource.',
    ], 401);
}
```

## Request ID Middleware

```php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Support\Str;

class RequestIdMiddleware
{
    public function handle($request, Closure $next)
    {
        $requestId = $request->header('X-Request-ID') ?? Str::uuid()->toString();
        $request->headers->set('X-Request-ID', $requestId);

        $response = $next($request);
        $response->headers->set('X-Request-ID', $requestId);

        return $response;
    }
}

// Register in app/Http/Kernel.php:
protected $middleware = [
    \App\Http\Middleware\RequestIdMiddleware::class,
];
```

## Task-Based Endpoint

```php
public function cancel(string $id, Request $request): JsonResponse
{
    // Domain exception → caught by Handler::render() above
    $order = $this->orderService->cancel($id, $request->user()->id);

    return response()->json(OrderResource::make($order), 200);
}
```
