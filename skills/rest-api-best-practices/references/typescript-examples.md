# TypeScript Examples

Examples using Express and NestJS. Patterns are the same; the framework determines the syntax.

## URL Structure and Route Definition

```typescript
// Express — routes map to resource actions
import express from "express";
const router = express.Router();

router.get("/orders",           listOrders);        // collection
router.post("/orders",          createOrder);       // create
router.get("/orders/:id",       getOrder);          // one resource
router.patch("/orders/:id",     updateOrder);       // partial update
router.delete("/orders/:id",    deleteOrder);       // remove

// Sub-collection
router.get("/orders/:id/items", listOrderItems);

// Task-based URLs — domain operations, not data mutations
router.post("/orders/:id/cancel", cancelOrder);
router.post("/orders/:id/ship",   shipOrder);

// NestJS — same structure via decorators
@Controller("orders")
export class OrdersController {
  @Get()        list()              {}
  @Post()       create()            {}
  @Get(":id")   findOne()           {}
  @Patch(":id") update()            {}
  @Delete(":id") remove()           {}
  @Post(":id/cancel") cancel()      {}
  @Post(":id/ship")   ship()        {}
}
```

## Status Codes in Responses

```typescript
// 200 OK — successful GET
res.status(200).json(order);

// 201 Created — successful POST with Location header
res.status(201)
  .header("Location", `/orders/${order.id}`)
  .json(order);

// 204 No Content — DELETE or PUT with no body
res.status(204).send();

// 202 Accepted — async operation triggered
res.status(202).json({ message: "Order cancellation queued.", jobId: job.id });

// NestJS via decorators
@Post()
@HttpCode(201)
@Header("Location", ...)
create(@Body() dto: CreateOrderDto) { ... }
```

## Request Validation (Zod)

```typescript
import { z } from "zod";

const CreateOrderSchema = z.object({
  customerId: z.string().uuid(),
  items: z.array(z.object({
    productId: z.string().uuid(),
    quantity:  z.number().int().positive(),
  })).min(1),
  shippingAddress: z.object({
    street:     z.string().min(1),
    city:       z.string().min(1),
    postalCode: z.string().regex(/^\d{5}$/),
    country:    z.string().length(2),
  }),
});

async function createOrder(req: Request, res: Response) {
  const result = CreateOrderSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(422).json(validationProblem(result.error));
  }
  // result.data is fully typed
  const order = await orderService.create(result.data);
  res.status(201).header("Location", `/orders/${order.id}`).json(order);
}

// NestJS — class-validator + class-transformer
class CreateOrderDto {
  @IsUUID()
  customerId: string;

  @IsArray()
  @ValidateNested({ each: true })
  @Type(() => OrderItemDto)
  items: OrderItemDto[];
}
```

## Error Response Format (RFC 7807)

```typescript
interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  errors?: Array<{ field: string; message: string }>;
}

function problem(status: number, code: string, detail: string): ProblemDetails {
  return {
    type: `https://api.example.com/errors/${code.toLowerCase().replace(/_/g, "-")}`,
    title: code.replace(/_/g, " "),
    status,
    detail,
  };
}

function validationProblem(error: ZodError): ProblemDetails {
  return {
    type: "https://api.example.com/errors/validation-failed",
    title: "Validation Failed",
    status: 422,
    detail: "The request body contains fields that failed validation.",
    errors: error.errors.map(e => ({
      field:   e.path.join("."),
      message: e.message,
    })),
  };
}
```

## Domain Error Translation Middleware

```typescript
// Domain errors — no HTTP knowledge
class OrderNotFound extends Error {
  constructor(id: string) { super(`Order ${id} not found`); }
}
class OrderAlreadyCancelled extends Error {}
class InsufficientStock extends Error {
  constructor(public readonly shortfall: number) { super(); }
}

// Express error middleware — one place handles all errors
import { Request, Response, NextFunction } from "express";

app.use((err: Error, req: Request, res: Response, _next: NextFunction) => {
  if (err instanceof OrderNotFound)
    return res.status(404).json(problem(404, "ORDER_NOT_FOUND", err.message));
  if (err instanceof OrderAlreadyCancelled)
    return res.status(409).json(problem(409, "ORDER_ALREADY_CANCELLED", "This order has already been cancelled."));
  if (err instanceof InsufficientStock)
    return res.status(422).json(problem(422, "INSUFFICIENT_STOCK", `Stock is short by ${err.shortfall} units.`));
  if (err instanceof ZodError)
    return res.status(422).json(validationProblem(err));

  logger.error("Unhandled error", { err, path: req.path });
  return res.status(500).json(problem(500, "INTERNAL_ERROR", "An unexpected error occurred."));
});
```

## Pagination

```typescript
// Query params parsed and validated
const PaginationSchema = z.object({
  page:    z.coerce.number().int().positive().default(1),
  perPage: z.coerce.number().int().positive().max(100).default(25),
});

async function listOrders(req: Request, res: Response) {
  const { page, perPage } = PaginationSchema.parse(req.query);
  const offset = (page - 1) * perPage;

  const [orders, total] = await orderRepo.findMany({ offset, limit: perPage });
  const totalPages = Math.ceil(total / perPage);
  const base = `${req.baseUrl}/orders`;

  const links: string[] = [
    `<${base}?page=1&perPage=${perPage}>; rel="first"`,
    `<${base}?page=${totalPages}&perPage=${perPage}>; rel="last"`,
  ];
  if (page > 1)          links.push(`<${base}?page=${page - 1}&perPage=${perPage}>; rel="prev"`);
  if (page < totalPages) links.push(`<${base}?page=${page + 1}&perPage=${perPage}>; rel="next"`);

  res
    .header("Link", links.join(", "))
    .header("X-Total-Count", String(total))
    .status(200)
    .json(orders);
}
```

## Filtering and Sorting

```typescript
const OrderFilterSchema = z.object({
  status:    z.enum(["pending", "confirmed", "shipped", "cancelled"]).optional(),
  customerId: z.string().uuid().optional(),
  createdAfter:  z.string().datetime().optional(),
  createdBefore: z.string().datetime().optional(),
  sort:      z.enum(["createdAt", "total", "status"]).default("createdAt"),
  order:     z.enum(["asc", "desc"]).default("desc"),
});

async function listOrders(req: Request, res: Response) {
  const filter = OrderFilterSchema.parse(req.query);
  const orders = await orderRepo.findMany(filter);
  res.json(orders);
}
```

## Authentication Middleware (JWT)

```typescript
import jwt from "jsonwebtoken";

function authenticate(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith("Bearer ")) {
    return res.status(401).json(problem(401, "UNAUTHORIZED", "Bearer token required."));
  }

  const token = authHeader.slice(7);
  try {
    const payload = jwt.verify(token, process.env.JWT_PUBLIC_KEY!, { algorithms: ["RS256"] });
    req.user = payload as AuthenticatedUser;
    next();
  } catch {
    return res.status(401).json(problem(401, "UNAUTHORIZED", "Invalid or expired token."));
  }
}

// Apply to protected routes
router.use(authenticate);
router.get("/orders", listOrders);
```

## Task-Based Endpoint

```typescript
// POST /orders/:id/cancel — domain operation, not a PATCH
async function cancelOrder(req: Request, res: Response, next: NextFunction) {
  try {
    const order = await orderService.cancel(req.params.id, req.user!.id);
    res.status(200).json(order);
  } catch (err) {
    next(err); // passed to error middleware
  }
}

// Service — enforces business rules
class OrderService {
  async cancel(orderId: string, requestedBy: string): Promise<Order> {
    const order = await this.orderRepo.findById(orderId);
    if (!order) throw new OrderNotFound(orderId);
    if (order.status === "shipped") throw new OrderAlreadyCancelled();
    order.cancel(requestedBy);
    await this.orderRepo.save(order);
    await this.eventBus.publish(order.pullDomainEvents());
    return order;
  }
}
```

## NestJS Full Example

```typescript
@Controller("v1/orders")
@UseGuards(JwtAuthGuard)
export class OrdersController {
  constructor(private readonly orderService: OrderService) {}

  @Get()
  async list(@Query() query: ListOrdersDto): Promise<PaginatedResponse<OrderView>> {
    return this.orderService.list(query);
  }

  @Post()
  @HttpCode(201)
  async create(
    @Body() dto: CreateOrderDto,
    @Res({ passthrough: true }) res: Response,
  ): Promise<OrderView> {
    const order = await this.orderService.create(dto);
    res.header("Location", `/v1/orders/${order.id}`);
    return order;
  }

  @Post(":id/cancel")
  async cancel(
    @Param("id") id: string,
    @CurrentUser() user: AuthUser,
  ): Promise<OrderView> {
    return this.orderService.cancel(id, user.id);
  }
}

// NestJS exception filter — translates domain errors globally
@Catch()
export class DomainExceptionFilter implements ExceptionFilter {
  catch(exception: Error, host: ArgumentsHost) {
    const res = host.switchToHttp().getResponse<Response>();
    const body = toProblemDetails(exception);
    res.status(body.status).json(body);
  }
}
```
