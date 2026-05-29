# Clojure — Functional Programming Examples

Concepts covered: pure functions, threading macros (pipe), currying/partial, nil handling, error handling, immutable data, higher-order functions, records/maps, side effect boundary.

Clojure is a dynamic, LISP-family functional language on the JVM. All data structures are persistent and immutable by default.

---

## Pure Functions and Referential Transparency

```clojure
;; All Clojure functions are pure unless they call side-effecting functions
;; No mutation of arguments — always return new values

(defn apply-discount [rate price]
  (* price (- 1 rate)))

;; apply-discount is referentially transparent:
;; (apply-discount 0.1 100) => 90.0   always

(defn add-item [cart item]
  (update cart :items conj item))
;; conj returns a new collection — cart is unchanged
```

---

## Threading Macros (Pipe)

```clojure
;; -> threads value as the FIRST argument (left-to-right)
(defn process-order [order]
  (-> order
      (update :items (partial filter :active))
      (assoc :total (calculate-total (:items order)))
      (apply-tax 0.21)
      format-for-response))

;; ->> threads value as the LAST argument — works naturally with sequence fns
(defn summarize-active-orders [orders]
  (->> orders
       (filter :active)
       (map :total)
       (reduce + 0)))

;; as-> threads the value as a named binding for mixed argument positions
(as-> user $
  (assoc $ :email (str/lower-case (:email $)))
  (update $ :name str/trim)
  (validate-user $))

;; some-> short-circuits on nil (like Maybe chaining)
(defn get-city [user]
  (some-> user :address :city))
```

---

## Currying and Partial Application

```clojure
;; Clojure is not auto-curried, but partial is built-in
(def apply-ten-percent (partial apply-discount 0.1))
(apply-ten-percent 200) ; 180.0

;; Anonymous function shorthand
(def double (partial * 2))
(map double [1 2 3]) ; (2 4 6)

;; Closures as partial application
(defn make-tax-fn [rate]
  (fn [price] (* price (+ 1 rate))))

(def add-vat (make-tax-fn 0.21))
(add-vat 100) ; 121.0

;; comp — right-to-left composition
(def process-email
  (comp str/lower-case str/trim))

(process-email "  Alice@Example.com  ") ; "alice@example.com"
```

---

## Nil Handling (Clojure's Maybe)

```clojure
;; Clojure uses nil as the "nothing" value
;; nil punning: most core functions handle nil gracefully

;; get returns nil if key not found — safe
(get {:name "Alice"} :email) ; nil
(get {:name "Alice"} :name)  ; "Alice"

;; some-> short-circuits the chain when nil is encountered
(defn get-city [user]
  (some-> user
          :address
          :city
          str/trim))

;; get-in — safe nested access (returns nil if any key missing)
(defn get-city [user]
  (get-in user [:address :city]))

;; fnil — wrap a function to replace nil with a default
(def safe-inc (fnil inc 0))
(safe-inc nil) ; 1
(safe-inc 5)   ; 6

;; when-let — execute body only when binding is non-nil
(defn display-city [user]
  (if-let [city (get-city user)]
    (str "City: " city)
    "City unknown"))
```

---

## Error Handling — Result-style with maps

```clojure
;; Clojure convention: return {:ok true :value v} or {:ok false :error e}
(defn validate-email [email]
  (if (str/includes? email "@")
    {:ok true  :value (str/lower-case email)}
    {:ok false :error "Invalid email"}))

(defn validate-age [age]
  (if (and (integer? age) (<= 0 age 150))
    {:ok true  :value age}
    {:ok false :error "Age must be 0-150"}))

(defn parse-user [{:keys [email age]}]
  (let [email-r (validate-email email)
        age-r   (validate-age age)]
    (cond
      (not (:ok email-r)) email-r
      (not (:ok age-r))   age-r
      :else {:ok true :value {:email (:value email-r) :age (:value age-r)}})))

;; With clojure.spec for richer validation
(require '[clojure.spec.alpha :as s])
(s/def ::email (s/and string? #(str/includes? % "@")))
(s/def ::age   (s/and integer? #(<= 0 % 150)))
(s/def ::user  (s/keys :req-un [::email ::age]))

(s/valid? ::user {:email "alice@example.com" :age 30}) ; true
(s/explain ::user {:email "notanemail" :age 30})
```

---

## Immutable Data Structures

```clojure
;; All Clojure data structures are persistent (immutable)
;; Operations return new values — the original is unchanged

(def user {:id "1" :name "Alice" :email "alice@example.com"})

;; assoc — returns new map with key updated
(def updated (assoc user :email "new@example.com"))
user    ; still {:id "1" :name "Alice" :email "alice@example.com"}
updated ; {:id "1" :name "Alice" :email "new@example.com"}

;; assoc-in — nested update
(def user-with-address (assoc user :address {:city "Madrid" :zip "28001"}))
(assoc-in user-with-address [:address :city] "Barcelona")

;; update — apply a function to an existing value
(update user :name str/upper-case)  ; {:name "ALICE" ...}

;; dissoc — remove a key
(dissoc user :email)

;; merge — combine maps (rightmost wins)
(merge user {:email "new@example.com" :role :admin})

;; Persistent vectors
(def items [1 2 3])
(conj items 4)   ; [1 2 3 4]  — items is still [1 2 3]
(pop items)      ; [1 2]
```

---

## Higher-Order Functions

```clojure
;; map — transform each element (returns lazy sequence)
(map #(* 2 %) [1 2 3])           ; (2 4 6)
(map :total orders)               ; extracts :total from each map

;; filter — select by predicate
(filter :active orders)           ; orders where :active is truthy
(filter #(> (:total %) 100) orders)

;; reduce — fold to a single value
(reduce + 0 [1 2 3 4 5])         ; 15
(reduce (fn [m item] (assoc m (:id item) item)) {} items) ; index by id

;; mapcat (= flatMap) — map then flatten one level
(mapcat :tags posts)              ; all tags from all posts

;; keep — like map but drops nils
(keep :city addresses)            ; only non-nil cities

;; group-by — partition by key function
(group-by :status orders)         ; {"active" [...] "cancelled" [...]}

;; sort-by — sort by key or function
(sort-by :total orders)
(sort-by :total > orders)         ; descending

;; take, drop, partition, take-while, drop-while
(->> (range 100)
     (filter even?)
     (take 5))                    ; (0 2 4 6 8)

;; Transducers — composable transforms, no intermediate collections
(def active-totals
  (comp (filter :active)
        (map :total)))

(transduce active-totals + 0 orders)  ; sum of active totals, one pass
```

---

## Sum Types — Records and Protocols

```clojure
;; Clojure uses maps with a :type key as tagged unions
(defn make-pending [created-at]
  {:type :pending :created-at created-at})

(defn make-shipped [created-at tracking-code]
  {:type :shipped :created-at created-at :tracking-code tracking-code})

(defn make-cancelled [created-at reason]
  {:type :cancelled :created-at created-at :reason reason})

(defn describe-status [status]
  (case (:type status)
    :pending   "Awaiting shipment"
    :shipped   (str "Shipped: " (:tracking-code status))
    :cancelled (str "Cancelled: " (:reason status))
    (throw (ex-info "Unknown status" {:status status}))))

;; Multimethods — dispatch on data, not class hierarchy
(defmulti area :shape)
(defmethod area :circle    [{:keys [radius]}] (* Math/PI radius radius))
(defmethod area :rectangle [{:keys [width height]}] (* width height))

(area {:shape :circle :radius 5})       ; 78.54...
(area {:shape :rectangle :width 4 :height 6}) ; 24
```

---

## Side Effect Boundary

```clojure
;; Pure core — all logic, no I/O
(defn process-registration [existing-emails input]
  (let [email (-> input :email str/lower-case str/trim)]
    (cond
      (not (str/includes? email "@"))
      {:ok false :error "Invalid email"}

      (contains? existing-emails email)
      {:ok false :error "Email already registered"}

      :else
      {:ok true :value {:id (str (java.util.UUID/randomUUID))
                        :email email
                        :created-at (java.time.Instant/now)}})))

;; Impure shell — thin I/O layer
(defn register-user! [input]
  (let [existing-emails (db/all-emails)                ; I/O
        result          (process-registration existing-emails input)]  ; pure
    (when (:ok result)
      (db/save-user! (:value result)))                 ; I/O
    result))

;; Dependency injection via function arguments
(defn register-user!
  ([input] (register-user! db/all-emails db/save-user! input))
  ([fetch-emails save-user! input]
   (let [existing-emails (fetch-emails)
         result          (process-registration existing-emails input)]
     (when (:ok result) (save-user! (:value result)))
     result)))
```
