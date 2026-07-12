# Week 4 — Supervised & Unsupervised Learning
## Slide-by-Slide Technical Companion

This document walks through every slide of the *Week 4* deck in detail: what the slide says,
the mathematics behind it, the reasoning for why the concept is defined that way, and how it
connects to the accompanying notebook. Read it alongside the deck — each section heading below
matches a slide title.

---

## Slide 1 — Title: "Supervised & Unsupervised Learning"

**What it says:** This is the opener. It frames Week 4 as Phase 2's foundation week, covering
four pillars — Supervised Learning, Unsupervised Learning, Train/Test Split, Evaluation Metrics
— that everything later in the ML/DL phase depends on.

**Why these four, in this order?** They form a dependency chain:

1. You can't evaluate a model (pillar 4) until you've split data into train/test (pillar 3).
2. You can't decide *how* to split or evaluate until you know whether your problem is
   supervised or unsupervised (pillars 1–2), because the two paradigms use fundamentally
   different evaluation strategies (ground-truth comparison vs. structural/geometric scoring).

**Technical takeaway:** nothing mathematical yet — this slide is purely organizational. Its job
is to set expectations: by the end of Week 4 you should be able to look at *any* new dataset and
answer "is this supervised or unsupervised, how would I split it, and how would I know if my
model is any good?"

---

## Slide 2 — "Week 4 at a glance"

**What it says:** A four-row summary table restating the pillars with one-line definitions:

| # | Topic | One-line definition |
|---|---|---|
| 01 | Supervised Learning | Learn a mapping from labelled examples (X → y) |
| 02 | Unsupervised Learning | Find structure in data with no labels at all |
| 03 | Train / Test Split | Estimate how a model performs on unseen data |
| 04 | Evaluation Metrics | Turn predictions into a number we can trust |

**Technical takeaway:** Notice the phrase "X → y" for supervised learning. This is standard ML
notation:
- **X** (capital, often bold **X**) denotes the **feature matrix** — one row per example, one
  column per feature. If you have *n* examples and *p* features, X is an *n × p* matrix.
- **y** (lowercase) denotes the **target vector** — one label per example, so a length-*n*
  vector.
- The arrow X → y is shorthand for "a function that consumes a row of X and outputs a
  prediction of the corresponding entry in y."

Unsupervised learning drops y entirely — you only ever work with X. That single difference is
what forces the two paradigms to use completely different evaluation approaches later
(Slides 10–11 vs. the silhouette-score discussion under Slide 6/9's family of ideas).

---

## Slide 3 — "Why learn from data at all?"

**What it says:** Contrasts *classical programming* (`Rules + Data → Output`) against
*machine learning* (`Data + Output → Rules`).

**The reasoning, unpacked:**

In classical programming, a human encodes explicit logic:

```
if income > 50000 and credit_score > 700:
    approve_loan()
else:
    reject_loan()
```

This works when:
- The relationship between inputs and outputs is simple enough for a human to state exactly.
- The rules don't need to adapt as new patterns emerge in the data.

It breaks down when the *true* decision boundary is too complex or too subtle for a human to
write by hand — e.g., "is this a photo of a cat?" There is no clean `if/else` chain over pixel
values that captures "cat-ness."

**Machine learning inverts the process.** Instead of a human supplying rules, we supply:
- **Data** — many examples of inputs.
- **Output** — the known correct answer for each of those inputs (in the supervised case).

...and let an algorithm *search* for the rule (technically, the function `f` and its
parameters `θ`) that best reproduces the known outputs. This is only possible because we
can turn "find good rules" into an **optimization problem** — which is exactly what Slide 4
formalizes.

**Trade-off named on the slide:** ML needs "enough representative data" and requires that we
"measure whether the learned rule generalises." Both concerns reappear as entire sections later
(train/test split, evaluation metrics) — this slide is foreshadowing why Slides 8–11 exist.

---

## Slide 4 — "Supervised Learning — the concept"

**What it says:** Every training example is a pair `(x, y)`. The algorithm's job is to find a
function `f` mapping `x → ŷ` (predicted y) such that `ŷ` is close to the true `y`, on data the
model hasn't seen. The central formula shown is:

```
f̂ = argmin_θ  (1/n) Σᵢ₌₁ⁿ  L( yᵢ , f(xᵢ) )
```

**Breaking this formula down term by term:**

- **`f`** — the model itself: a function that takes a feature vector `x` and returns a
  prediction. Its exact *shape* depends on the algorithm choice (a straight line for linear
  regression, a set of nested if/else splits for a decision tree, a weighted sum passed through
  a sigmoid for logistic regression, etc.).
- **`θ` (theta)** — the model's *parameters*: the numbers that get adjusted during training.
  For linear regression, `θ` is the vector of coefficients (slopes) plus an intercept. For a
  neural network, `θ` is every weight and bias in the network.
- **`L(yᵢ, f(xᵢ))`** — the **loss function**, evaluated on a single example `i`. It measures
  "how wrong" one prediction is. Different problems use different losses:
  - **Squared error** (regression): `L = (yᵢ − f(xᵢ))²`. Squaring makes the loss always
    non-negative and penalizes large errors much more than small ones (an error of 10 costs
    100, an error of 2 costs only 4 — 25× less for 5× the raw error).
  - **Cross-entropy / log loss** (classification): for binary classification with predicted
    probability `p = f(xᵢ)`,
    `L = −[ yᵢ·log(p) + (1−yᵢ)·log(1−p) ]`.
    This penalizes *confident, wrong* predictions extremely harshly — predicting `p = 0.99` for
    an example that's actually class 0 produces a huge loss (`−log(0.01) ≈ 4.6`), while a timid
    wrong prediction (`p = 0.51`) is penalized much less. This property pushes the model toward
    well-calibrated probabilities, not just "eventually correct" ones.
- **`(1/n) Σᵢ₌₁ⁿ`** — average the per-example loss over all `n` training examples. This is the
  **empirical risk** — our best estimate, using only the data we have, of how wrong the model
  is "in general."
- **`argmin_θ`** — search over all possible parameter values `θ` and return the ones that make
  the average loss smallest. This is literally the definition of "training a model": an
  optimization search, usually performed with **gradient descent** — repeatedly nudging `θ` in
  the direction that decreases the loss fastest, using the gradient (vector of partial
  derivatives) `∇_θ L`.

**Why frame learning this way (the "reasoning" callout on the slide)?** Because loss functions
are (usually) differentiable, we can compute their gradient with respect to every parameter.
That gradient tells us exactly which direction to move each parameter to reduce error. This is
what makes training *automatic* rather than manual — the same `argmin` framework scales from a
two-parameter linear regression up to a billion-parameter neural network, because the underlying
optimization principle (follow the gradient downhill) doesn't change.

**Real-world example on the slide:** A spam filter learns from millions of `(email, label)`
pairs where label ∈ {spam, not-spam}. Each email is turned into a feature vector `x` (e.g. word
frequencies), and the filter minimizes cross-entropy loss across the whole training set to learn
a rule that generalizes to brand-new incoming mail.

---

## Slide 5 — "Two flavours of supervised learning"

**What it says:** The type of the target `y` determines whether you're doing **classification**
(discrete `y`) or **regression** (continuous `y`).

**Classification**, technically:
- `y ∈ {c₁, c₂, ..., cₖ}` — a finite set of categories.
- Output is either a hard label (`ŷ = c₂`) or, more usefully, a probability distribution over
  classes (`P(y=c₁|x)=0.1, P(y=c₂|x)=0.7, P(y=c₃|x)=0.2`), from which the hard label is taken
  as the class with highest probability: `ŷ = argmax_c P(y=c|x)`.
- The Iris example: predict species (setosa / versicolor / virginica) from 4 numeric
  measurements — a **3-class classification** problem.
- The Titanic example: predict `survived ∈ {0, 1}` — a **binary classification** problem.

**Regression**, technically:
- `y ∈ ℝ` — any real number (or a bounded range of real numbers).
- Output is a single real number `ŷ`, and "closeness" is measured by *distance* (e.g. squared
  error) rather than *exact match*. A prediction of $302,000 for a true price of $300,000 is
  "almost right" in a way that doesn't exist in classification — there, you're either the
  correct class or you're not (partial credit for "close" classes isn't automatic).
- The Boston Housing example: predict median home value (a dollar amount) from features like
  room count, crime rate, and location.

**Why this distinction matters technically:** it determines *everything downstream* — which
loss function you train with (cross-entropy vs. squared error), which final-layer activation
a neural network needs (softmax vs. linear/identity), and which evaluation metrics apply
(Slide 10 vs. Slide 11). Get this classification wrong at the start and every later step
breaks.

---

## Slide 6 — "Unsupervised Learning — the concept"

**What it says:** No label `y` exists — only features `X`. The algorithm must discover
structure that already exists in the data. The example objective given is **K-Means
clustering**:

```
min_μ  Σₖ₌₁ᴷ  Σ (over xᵢ in cluster k)  ‖ xᵢ − μₖ ‖²
```

**Breaking this down:**

- **`K`** — the number of clusters, chosen in advance (a hyperparameter, not learned).
- **`μₖ`** (mu-k) — the **centroid** of cluster `k`: the mean position of all points currently
  assigned to that cluster. It's a vector in the same feature space as the data points.
- **`‖xᵢ − μₖ‖²`** — the squared **Euclidean distance** between point `xᵢ` and centroid `μₖ`.
  For 2D points this is just `(x₁−μ₁)² + (x₂−μ₂)²` (Pythagoras); it generalizes to any number
  of dimensions by summing squared differences across every feature.
- **Double sum** — for each cluster `k`, sum the squared distance of every point currently
  assigned to that cluster to its centroid, then sum that across all `K` clusters. This total
  is called the **within-cluster sum of squares (WCSS)** or **inertia**.
- **`min_μ`** — search over centroid positions to make total WCSS as small as possible: i.e.,
  make every point as close as possible to the center of its own group.

**The algorithm (Lloyd's algorithm), step by step:**
1. **Initialize**: pick `K` starting centroid positions (often `K` random data points).
2. **Assign step**: for every point, compute its distance to all `K` centroids and assign it
   to the nearest one.
3. **Update step**: recompute each centroid as the mean of all points now assigned to it.
4. **Repeat** steps 2–3 until assignments stop changing (convergence).

This alternating assign/update process is guaranteed to *decrease* (or keep constant) the WCSS
objective every iteration, so it always converges — though not necessarily to the *global*
minimum (different random initializations can land in different local minima, which is why
scikit-learn's `KMeans` runs multiple initializations — `n_init` — and keeps the best one).

**Why does this work with no labels?** The core assumption is that geometric closeness in
feature space corresponds to real-world similarity. This is a *weaker* assumption than
supervised learning requires (which needs actual labelled examples of "similarity"), which is
why unsupervised methods are cheap to apply broadly — but also why the resulting clusters are
only as meaningful as that closeness assumption holds for your specific chosen features.

**Real-world example on the slide:** a retailer clusters shoppers by spending score and income
(no predefined "correct" segments exist) to design targeted promotions. The clusters that
K-Means finds *become* the segments — there's no ground truth to check them against, only
whether they're useful and well-separated.

---

## Slide 7 — "Supervised vs. Unsupervised" (comparison table)

**What it says:** A direct side-by-side of the two paradigms across six dimensions: training
data, goal, example algorithms, feedback signal, evaluation, and this week's data.

**Technical elaboration on each row:**

- **Training data** — Supervised needs `(x, y)` pairs; unsupervised needs only `X`. This single
  fact is the root cause of every other row in the table.
- **Feedback signal** — Supervised gets a *direct* signal: compare `ŷ` to the *known* true `y`
  and compute an exact error. Unsupervised gets only an *indirect* signal: geometric or
  statistical properties of the data itself (e.g., "are points within a cluster close together
  and points between clusters far apart?") — there's no ground truth to check against.
- **Evaluation** — This is the most consequential difference. Supervised evaluation
  (Slides 10–11) always reduces to "compare predictions against known answers." Unsupervised
  evaluation (introduced via the silhouette score in the notebook) can only ever measure
  *internal consistency* of the discovered structure, never "correctness," because correctness
  is undefined without labels.
- **Example algorithms** — Linear/Logistic Regression and Decision Trees are supervised because
  they're trained by minimizing loss against known `y`. K-Means, DBSCAN, and PCA are
  unsupervised because none of them ever reference a label during training.

**Why put this on its own slide?** In practice, the very first question to ask about any new
dataset is "do I have labels?" That answer determines which half of this table you live in for
the rest of the project — which algorithms are even eligible, and which evaluation approach is
valid.

---

## Slide 8 — "Train / Test Split — why we hide data from the model"

**What it says:** If we test a model on the data it trained on, high accuracy only proves
memorization, not generalization. The slide visualizes an 80/20 split and introduces the
**generalization gap**:

```
Gap = Error_test − Error_train
```

**Unpacking the reasoning:**

Suppose you train a model and then evaluate it on the *exact same* rows it learned from. A
sufficiently flexible model (e.g., a very deep decision tree) can achieve near-zero error simply
by "memorizing" the answer for every training row — including its noise and idiosyncrasies —
without having learned anything that transfers to new data. This is why we **hold out a test
set**: rows the model never sees during training, used *only* at the end to estimate real-world
performance.

**Interpreting the gap:**

- **Small gap** (test error ≈ train error): the model generalizes well — whatever it learned
  from training data transfers to new data.
- **Large gap** (test error ≫ train error): **overfitting**. The model has fit patterns specific
  to the training set — including noise — that don't hold in general. This corresponds to
  **high variance**: the model is highly sensitive to exactly which training rows it happened
  to see.
- **High error on *both* sets**: **underfitting**. The model is too simple to capture even the
  patterns that *do* generalize. This corresponds to **high bias**: systematic error regardless
  of which data it's trained or tested on.

**The bias–variance decomposition (the deeper math underneath this slide):**

For a regression problem with squared-error loss, the expected test error at a point `x` can be
decomposed exactly as:

```
E[(y − f̂(x))²] = Bias[f̂(x)]² + Var[f̂(x)] + σ²
```

- **`Bias[f̂(x)]²`** — how far the *average* prediction (averaged over many possible training
  sets) is from the true function. High bias = systematically wrong, "too simple" models
  (e.g., fitting a straight line to a clearly curved relationship).
- **`Var[f̂(x)]`** — how much the prediction *changes* depending on which particular training
  set was used. High variance = "too flexible" models that latch onto training-set-specific
  noise.
- **`σ²`** — irreducible noise inherent in the data-generating process itself. No model, no
  matter how good, can eliminate this term.

This decomposition is why "just make the model more complex" isn't a universal fix: complexity
trades bias for variance. The train/test split (and its generalization gap) is the practical
tool for detecting *which* regime — high bias or high variance — a given model is in, so you
know which direction to adjust (simplify to fix variance, add complexity/features to fix bias).

**Why 80/20 (or 70/30)?** It's a practical trade-off: more training data generally produces a
better-fit model, but the test set still needs to be large enough that its error estimate isn't
itself noisy from too few samples. There's no universally "correct" ratio — it depends on total
dataset size (very large datasets can afford smaller test fractions in absolute terms).

**Real-world stakes example on the slide:** A hospital readmission model that shows 95% accuracy
on training data but was never evaluated on held-out patients could be dangerously overfit —
its real-world performance is simply unknown until tested on unseen data, and the consequences
of that unknown are not abstract.

---

## Slide 9 — "Going further — k-fold cross-validation"

**What it says:** A single train/test split's estimate depends on which rows happened to land in
the test set — it can be "lucky" or "unlucky." **k-fold cross-validation** averages over `k`
different splits for a more reliable estimate:

```
CV Score = (1/k) Σₖ₌₁ᴷ Error(fold k)
```

**How k-fold CV works, mechanically:**

1. Split the full dataset into `k` equal-sized, non-overlapping "folds" (the slide visualizes
   `k = 5`).
2. For each fold `i` from 1 to `k`:
   - Treat fold `i` as the **test set**.
   - Treat the remaining `k − 1` folds combined as the **training set**.
   - Train a fresh model and record its error on fold `i`.
3. Average the `k` recorded error values to get the final CV score.

**Why is this better than one split?** Every single row gets used as test data *exactly once*
across the `k` rounds — no data is "wasted" sitting permanently in a test set that's never
trained on, and no data is permanently locked out of ever being tested on. Because the reported
score is an *average* over `k` different train/test partitions, it's far less sensitive to the
specific luck of any one split. The standard deviation across the `k` fold-scores also gives you
a sense of how *stable* the estimate is — a tight spread means consistent performance, a wide
spread means the model's quality is sensitive to exactly which data it sees.

**Trade-off:** k-fold CV costs `k×` the compute of a single train/test split, since a full model
must be trained from scratch for every fold. This is why single splits remain common for
quick iteration, while k-fold CV is preferred for a final, trustworthy performance estimate or
for comparing between candidate models/hyperparameters.

---

## Slide 10 — "Evaluation Metrics — Classification"

**What it says:** Introduces the **confusion matrix** and four key formulas: Accuracy,
Precision, Recall, and F1-score.

**The confusion matrix**, for binary classification:

| | Predicted + | Predicted − |
|---|---|---|
| **Actual +** | True Positive (TP) | False Negative (FN) |
| **Actual −** | False Positive (FP) | True Negative (TN) |

Every prediction the model makes falls into exactly one of these four cells:
- **TP** — model predicted positive, and it actually was positive. Correct.
- **TN** — model predicted negative, and it actually was negative. Correct.
- **FP** ("false alarm" / Type I error) — model predicted positive, but it was actually
  negative.
- **FN** ("missed case" / Type II error) — model predicted negative, but it was actually
  positive.

**The four formulas, and *why* each is defined the way it is:**

```
Accuracy  = (TP + TN) / (TP + TN + FP + FN)
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1-score  = 2 × (Precision × Recall) / (Precision + Recall)
```

- **Accuracy** — the fraction of *all* predictions that were correct. Simple and intuitive, but
  it treats every class as equally important and equally frequent — which is exactly what
  breaks it on imbalanced data (see below).
- **Precision** — *of everything the model flagged as positive, how much was actually
  positive?* Its denominator (`TP + FP`) is "everything predicted positive." Low precision means
  lots of false alarms. Precision is what you optimize for when a false positive is costly
  (e.g. flagging a legitimate transaction as fraud and blocking a real customer).
- **Recall** (a.k.a. sensitivity or true positive rate) — *of everything that was actually
  positive, how much did the model catch?* Its denominator (`TP + FN`) is "everything that was
  truly positive." Low recall means missed cases. Recall is what you optimize for when a false
  negative is costly (e.g. missing an actual cancer diagnosis).
- **F1-score** — the **harmonic mean** of precision and recall (note: harmonic mean, not
  arithmetic mean). The harmonic mean is used specifically because it heavily penalizes a large
  imbalance between the two: if precision = 1.0 but recall = 0.0, the arithmetic mean would
  report a misleadingly high 0.5, while the harmonic mean correctly reports F1 = 0. F1 is useful
  as a single number when both false positives and false negatives matter and you want to
  balance them rather than choosing one to prioritize.

**Why not just use accuracy? (the slide's own callout, expanded)**

On the Titanic dataset, roughly 62% of passengers did not survive. A trivial model that *always*
predicts "did not survive," regardless of input, would score **62% accuracy** while having
learned nothing and being operationally useless — it can never correctly identify a single
survivor. This is the textbook failure mode of accuracy on **imbalanced datasets**: when one
class dominates, a model can score deceptively well by simply ignoring the minority class
entirely. Precision, recall, and F1 — computed with respect to the minority ("survived") class
— expose this failure immediately, because a model that never predicts "survived" will have
**zero recall** for that class no matter how high its accuracy looks.

**Multi-class note (relevant to the Iris example):** with more than two classes, there's no
single TP/FP/FN — precision and recall are computed *per class* (treating that class as
"positive" and all others as "negative"), then combined:
- **Macro-average**: compute the metric per class, then average the class-level scores with
  equal weight — appropriate when every class matters equally regardless of size (as with the
  balanced, 50-per-class Iris dataset).
- **Weighted average**: same per-class computation, but the average is weighted by how many
  true examples each class has — appropriate when larger classes should dominate the summary
  score.

---

## Slide 11 — "Evaluation Metrics — Regression"

**What it says:** Since regression targets are continuous, we measure the *distance* between
predicted and actual values rather than right/wrong. Four metrics are given:

```
MAE  = (1/n) Σ | yᵢ − ŷᵢ |
MSE  = (1/n) Σ ( yᵢ − ŷᵢ )²
RMSE = √MSE
R²   = 1 − SS_res / SS_tot
```

**Term by term:**

- **MAE (Mean Absolute Error)** — average the *absolute value* of each error. It's expressed in
  the same units as `y` (e.g., dollars for a price-prediction model), which makes it easy to
  explain to a non-technical audience: "our price predictions are off by $12,000 on average."
  Because it uses absolute value rather than squaring, MAE treats a $50k miss and a $5k miss
  proportionally — it doesn't disproportionately punish large errors, making it more **robust
  to outliers** than MSE.
- **MSE (Mean Squared Error)** — average the *squared* error. Squaring makes large errors
  count disproportionately more: an error of 10 contributes 100 to the sum, while an error of 2
  contributes only 4 — the 5× larger raw error contributes 25× more to the total. This is
  useful when large mistakes are genuinely much worse than small ones (e.g. a medication-dosage
  model where a big miss is dangerous in a way a small miss isn't), but it also makes MSE
  sensitive to a small number of extreme outliers, which can dominate the whole metric.
- **RMSE (Root Mean Squared Error)** — the square root of MSE, which puts the metric back into
  the *original* units of `y` (since MSE's units are "squared dollars," which isn't
  interpretable on its own). RMSE is directly comparable to MAE: if RMSE is close to MAE, errors
  are fairly uniform in size; if RMSE is *much larger* than MAE, a few large outlier errors are
  dominating the score (because squaring amplifies them disproportionately before the square
  root is taken).
- **R² (coefficient of determination)** — reframes error in terms of **explained variance**.
  - `SS_res` (residual sum of squares) = `Σ(yᵢ − ŷᵢ)²` — the model's total squared error (same
    numerator logic as MSE, just not averaged).
  - `SS_tot` (total sum of squares) = `Σ(yᵢ − ȳ)²`, where `ȳ` is the mean of all true `y` values
    — this is the error a *naive baseline model* would produce if it always predicted the
    average value, ignoring every feature.
  - `R² = 1 − SS_res/SS_tot` therefore measures: what fraction of the variance in `y` does our
    model explain, relative to just guessing the average every time?
    - `R² = 1.0` → perfect predictions (`SS_res = 0`).
    - `R² = 0.0` → the model is exactly as good as always predicting the mean.
    - `R² < 0` → the model is *worse* than that naive baseline (it's possible, and a serious
      red flag if it happens).

**Why have four metrics instead of one?** Each answers a slightly different question, and
together they give a fuller picture: MAE for an intuitive "typical error size," RMSE alongside
MAE to detect whether outliers are dominating, MSE when large errors deserve extra
punishment during training or comparison, and R² to express performance as a
dataset-independent, unit-free percentage that's easy to compare across different problems.

---

## Slide 12 — "This week's project: Iris & Titanic Dataset Exploration"

**What it says:** A five-step workflow for the week's hands-on project:

1. **Load & inspect** — read both datasets; check shape, dtypes, missing values, class balance.
2. **Explore visually** — pairplots for Iris; survival rate by class/sex/age for Titanic.
3. **Split the data** — 80/20 train/test split, stratified by the target label.
4. **Fit a baseline model** — Logistic Regression / Decision Tree.
5. **Evaluate honestly** — confusion matrix, accuracy, precision, recall, F1, on the test set
   only.

**Technical notes on each step, tying back to earlier slides:**

- **Step 1** connects to Slide 3's point that real data isn't automatically clean — Titanic in
  particular has missing `age` and `deck` values that must be handled (typically via
  **imputation**, e.g. filling missing numeric values with the column median, which is robust to
  outlier-skewed distributions) before any model can be trained.
- **Step 2** is the practical check from Slide 4/5's framing: visualizing whether classes are
  separable (as with Iris's petal measurements) tells you up front whether the problem is
  "learnable" with the features you have.
- **Step 3**'s mention of **stratified** splitting is an important refinement of Slide 8's
  80/20 split: stratification ensures the *proportion* of each class is preserved in both the
  train and test sets. Without it, a small or unlucky split could leave a minority class
  underrepresented (or entirely absent) in the test set, making the resulting evaluation
  unreliable — especially critical for Titanic's imbalanced ~38%/62% survival split.
- **Step 4** applies Slide 4's `argmin` loss-minimization framework concretely: Logistic
  Regression minimizes cross-entropy loss via the sigmoid function
  `P(y=1|x) = 1/(1+e^(−θᵀx))`, while a Decision Tree instead greedily splits the feature space
  to minimize an impurity measure (like Gini impurity or entropy) at each node — a different
  optimization strategy but the same underlying goal of fitting `X → y`.
- **Step 5** applies Slide 10's metrics — critically, "on the test set only," directly enforcing
  the generalization principle from Slide 8: never use training performance to judge whether the
  model actually works.

**Why Iris *and* Titanic, rather than just one?** Iris is a clean, balanced, easily-separable
teaching dataset — ideal for learning the *mechanics* of a classification pipeline without
fighting messy data. Titanic then immediately stress-tests those same mechanics against missing
values, mixed data types (numeric + categorical), and a genuinely imbalanced target — forcing
the precision/recall/F1 concepts from Slide 10 to actually matter, rather than being an abstract
exercise.

---

## Slide 13 — "Key takeaways"

**What it says:** A four-point summary distilling the entire week:

1. Supervised learning minimises a loss function between predictions and known labels — it
   needs `(x, y)` pairs.
2. Unsupervised learning finds structure — like clusters — using only the features, with no
   labels required.
3. Always evaluate on held-out data. Train/test split (or k-fold CV) is what separates
   memorisation from generalisation.
4. Pick metrics that match the problem: accuracy can lie on imbalanced data — precision,
   recall, F1, MSE, R² tell the real story.

**Why this is the right summary (tying every prior slide together):**

- Point 1 is Slide 4's core formula (`argmin` loss minimization) restated in one sentence.
- Point 2 is Slide 6's K-Means objective restated — structure discovered from geometry alone,
  no ground truth involved.
- Point 3 is Slides 8–9's generalization-gap and cross-validation argument compressed: the
  single most important discipline in applied ML is *never* trusting a number computed on data
  the model has already seen.
- Point 4 is Slides 10–11's central lesson: no single metric is universally correct — the right
  metric depends on the cost structure of the real-world problem (is a false positive or a false
  negative worse? do large errors matter disproportionately more than small ones?).

**What comes next (as previewed on the slide):** Week 5 moves from *concepts* to *specific
algorithms* — Linear & Logistic Regression in more mathematical depth, plus K-Means and DBSCAN
for unsupervised clustering — applied to the Boston Housing and Mall Customers datasets. Every
tool introduced this week (train/test split, cross-validation, the classification and regression
metrics) will be used immediately to evaluate those new models, so this document's contents are
prerequisite knowledge for the rest of Phase 2.

---

### Quick-reference formula sheet

| Concept | Formula |
|---|---|
| Supervised learning objective | `θ̂ = argmin_θ (1/n) Σ L(yᵢ, f_θ(xᵢ))` |
| Sigmoid (logistic regression) | `P(y=1\|x) = 1 / (1 + e^(−θᵀx))` |
| Cross-entropy loss (binary) | `L = −[y·log(p) + (1−y)·log(1−p)]` |
| K-Means objective | `min_μ Σₖ Σ_{xᵢ∈Cₖ} ‖xᵢ − μₖ‖²` |
| Generalization gap | `Gap = Error_test − Error_train` |
| Bias–variance decomposition | `E[(y−f̂(x))²] = Bias² + Variance + σ²` |
| k-fold CV score | `CV = (1/k) Σₖ Error(fold k)` |
| Accuracy | `(TP+TN) / (TP+TN+FP+FN)` |
| Precision | `TP / (TP+FP)` |
| Recall | `TP / (TP+FN)` |
| F1-score | `2·(P·R) / (P+R)` |
| MAE | `(1/n) Σ \|yᵢ − ŷᵢ\|` |
| MSE | `(1/n) Σ (yᵢ − ŷᵢ)²` |
| RMSE | `√MSE` |
| R² | `1 − SS_res/SS_tot` |
| Silhouette score (per point) | `s(i) = (b(i) − a(i)) / max(a(i), b(i))` |

*End of document.*
