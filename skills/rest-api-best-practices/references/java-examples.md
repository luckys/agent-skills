# Java Examples

Examples using Spring Boot 3.x with Spring Web MVC.

## Route Definition and URL Structure

```java
package com.example.orders.api;

import org.springframework.web.bind.annotation.*;
import org.springframework.http.*;

@RestController
@RequestMapping("/v1/orders")
public class OrderController {

    @GetMapping                    public ResponseEntity<Page<OrderSummary>> list(...) {}
    @PostMapping                   public ResponseEntity<OrderResponse>      create(...) {}
    @GetMapping("/{id}")           public ResponseEntity<OrderResponse>      get(...) {}
    @PatchMapping("/{id}")         public ResponseEntity<OrderResponse>      update(...) {}
    @DeleteMapping("/{id}")        public ResponseEntity<Void>               delete(...) {}

    // Sub-collection
    @GetMapping("/{id}/items")     public ResponseEntity<List<OrderItem>>    listItems(...) {}

    // Task-based URLs — domain operations
    @PostMapping("/{id}/cancel")   public ResponseEntity<OrderResponse>      cancel(...) {}
    @PostMapping("/{id}/ship")     public ResponseEntity<OrderResponse>      ship(...) {}
}
```

## Status Codes in Responses

```java
@PostMapping
public ResponseEntity<OrderResponse> create(
    @RequestBody @Valid CreateOrderRequest body,
    UriComponentsBuilder uriBuilder
) {
    Order order = orderService.create(body);
    URI location = uriBuilder.path("/v1/orders/{id}").buildAndExpand(order.getId()).toUri();

    return ResponseEntity
        .created(location)      // 201 Created + Location header
        .body(OrderResponse.from(order));
}

@DeleteMapping("/{id}")
public ResponseEntity<Void> delete(@PathVariable String id) {
    orderService.delete(id);
    return ResponseEntity.noContent().build(); // 204 No Content
}

@PostMapping("/{id}/cancel")
public ResponseEntity<OrderResponse> cancel(@PathVariable String id, Authentication auth) {
    Order order = orderService.cancel(id, auth.getName());
    return ResponseEntity.ok(OrderResponse.from(order)); // 200 OK
}
```

## Request Validation (Bean Validation)

```java
import jakarta.validation.constraints.*;
import jakarta.validation.Valid;

public class CreateOrderRequest {

    @NotNull @Pattern(regexp = "^[0-9a-f-]{36}$")
    private String customerId;

    @NotNull @Size(min = 1, message = "must contain at least one item")
    @Valid
    private List<OrderItemRequest> items;

    @NotNull @Valid
    private ShippingAddressRequest shippingAddress;
}

public class OrderItemRequest {
    @NotNull @Pattern(regexp = "^[0-9a-f-]{36}$")
    private String productId;

    @NotNull @Min(1)
    private Integer quantity;
}

public class ShippingAddressRequest {
    @NotBlank private String street;
    @NotBlank private String city;
    @NotBlank private String postalCode;
    @NotBlank @Size(min = 2, max = 2) private String country;
}

// Spring validates automatically when @Valid is present on @RequestBody.
// MethodArgumentNotValidException → handled in exception handler below.
```

## Error Response Format (RFC 9457)

```java
package com.example.orders.api.error;

import java.util.List;
import org.springframework.http.MediaType;
import org.slf4j.MDC;

public record ProblemDetails(
    String type,
    String title,
    int    status,
    String detail,
    List<FieldError> errors
) {
    public record FieldError(String field, String message) {}

    public static ProblemDetails of(int status, String code, String detail) {
        String slug = code.toLowerCase().replace('_', '-');
        return new ProblemDetails(
            "https://api.example.com/errors/" + slug,
            code.replace('_', ' '),
            status,
            detail,
            null
        );
    }
}

// Global exception handler
@RestControllerAdvice
public class GlobalExceptionHandler {

    private static String publicValidationMessage(String code) {
        return switch (code) {
            case "NotNull", "NotBlank" -> "Required field.";
            case "Size" -> "Invalid length.";
            default -> "Invalid value.";
        };
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ProblemDetails> handleValidation(MethodArgumentNotValidException ex) {
        List<ProblemDetails.FieldError> errors = ex.getBindingResult()
            .getFieldErrors()
            .stream()
            .map(e -> new ProblemDetails.FieldError(e.getField(), publicValidationMessage(e.getCode())))
            .toList();

        ProblemDetails body = new ProblemDetails(
            "https://api.example.com/errors/validation-failed",
            "Validation Failed",
            422,
            "The request body contains fields that failed validation.",
            errors
        );
        return ResponseEntity.unprocessableEntity().contentType(MediaType.APPLICATION_PROBLEM_JSON).body(body);
    }

    @ExceptionHandler(OrderNotFoundException.class)
    public ResponseEntity<ProblemDetails> handleOrderNotFound(OrderNotFoundException ex) {
        return ResponseEntity.status(404)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(ProblemDetails.of(404, "ORDER_NOT_FOUND", "Order not found."));
    }

    @ExceptionHandler(OrderAlreadyCancelledException.class)
    public ResponseEntity<ProblemDetails> handleAlreadyCancelled(OrderAlreadyCancelledException ex) {
        return ResponseEntity.status(409)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(ProblemDetails.of(409, "ORDER_ALREADY_CANCELLED", "This order has already been cancelled."));
    }

    @ExceptionHandler(InsufficientStockException.class)
    public ResponseEntity<ProblemDetails> handleInsufficientStock(InsufficientStockException ex) {
        return ResponseEntity.status(422)
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(ProblemDetails.of(422, "INSUFFICIENT_STOCK",
                "Stock is short by " + ex.getShortfall() + " units."));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ProblemDetails> handleUnknown(Exception ex) {
        String requestId = MDC.get("requestId");
        safeExceptionLogger.capture(ex, requestId);
        return ResponseEntity.internalServerError()
            .contentType(MediaType.APPLICATION_PROBLEM_JSON)
            .body(ProblemDetails.of(500, "INTERNAL_ERROR", "An unexpected error occurred."));
    }
}
```

## Pagination

```java
import org.springframework.data.domain.*;
import org.springframework.data.web.PageableDefault;

@GetMapping
public ResponseEntity<List<OrderSummary>> list(
    @RequestParam(defaultValue = "1") int page,
    @RequestParam(name = "per_page", defaultValue = "25") int perPage,
    HttpServletResponse response
) {
    perPage = Math.min(perPage, 100);
    int offset = (page - 1) * perPage;

    PageResult<OrderSummary> result = orderRepo.findMany(offset, perPage);
    int totalPages = (int) Math.ceil((double) result.total() / perPage);
    String base = "/v1/orders";

    List<String> links = new ArrayList<>();
    links.add(String.format("<%s?page=1&per_page=%d>; rel=\"first\"", base, perPage));
    links.add(String.format("<%s?page=%d&per_page=%d>; rel=\"last\"", base, totalPages, perPage));
    if (page > 1)          links.add(String.format("<%s?page=%d&per_page=%d>; rel=\"prev\"", base, page - 1, perPage));
    if (page < totalPages) links.add(String.format("<%s?page=%d&per_page=%d>; rel=\"next\"", base, page + 1, perPage));

    response.setHeader("Link", String.join(", ", links));
    response.setHeader("X-Total-Count", String.valueOf(result.total()));

    return ResponseEntity.ok(result.items());
}
```

## Filtering and Sorting

```java
@GetMapping
public ResponseEntity<List<OrderSummary>> list(
    @RequestParam(required = false) OrderStatus status,
    @RequestParam(required = false) String customerId,
    @RequestParam(defaultValue = "createdAt") String sort,
    @RequestParam(defaultValue = "desc") String order,
    @RequestParam(defaultValue = "1") int page,
    @RequestParam(name = "per_page", defaultValue = "25") int perPage
) {
    // Validate sort field against allowlist
    if (!ALLOWED_SORT_FIELDS.contains(sort)) {
        throw new InvalidParameterException("sort", "must be one of: " + ALLOWED_SORT_FIELDS);
    }
    ...
}

private static final Set<String> ALLOWED_SORT_FIELDS = Set.of("createdAt", "total", "status");
```

## Authentication (Spring Security + JWT)

```java
// SecurityConfig.java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(AbstractHttpConfigurer::disable)
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/health/**").permitAll()
                .anyRequest().authenticated()
            )
            .oauth2ResourceServer(oauth2 -> oauth2
                .jwt(jwt -> jwt.decoder(jwtDecoder()))
            )
            .build();
    }
}

// Controller — access authenticated user
@PostMapping("/{id}/cancel")
public ResponseEntity<OrderResponse> cancel(
    @PathVariable String id,
    @AuthenticationPrincipal Jwt jwt
) {
    String userId = jwt.getSubject();
    Order order = orderService.cancel(id, userId);
    return ResponseEntity.ok(OrderResponse.from(order));
}
```

## Request ID Filter

```java
import jakarta.servlet.*;
import jakarta.servlet.http.*;
import org.springframework.stereotype.Component;
import java.util.UUID;

@Component
public class RequestIdFilter implements Filter {

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
        throws IOException, ServletException {

        HttpServletRequest  request  = (HttpServletRequest)  req;
        HttpServletResponse response = (HttpServletResponse) res;

        String upstreamRequestId = request.getHeader("X-Request-ID"); // validate/log separately if needed
        String requestId = UUID.randomUUID().toString();

        response.setHeader("X-Request-ID", requestId);

        // Put in MDC for structured logging
        try (var ignored = MDC.putCloseable("requestId", requestId)) {
            chain.doFilter(req, res);
        }
    }
}
```

## Task-Based Endpoint

```java
@PostMapping("/{id}/cancel")
public ResponseEntity<OrderResponse> cancel(
    @PathVariable String id,
    @AuthenticationPrincipal Jwt jwt
) {
    // Domain exceptions propagate to @RestControllerAdvice
    Order order = orderService.cancel(id, jwt.getSubject());
    return ResponseEntity.ok(OrderResponse.from(order));
}
```
