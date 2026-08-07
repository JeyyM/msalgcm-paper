# Comparative Metaheuristic Optimization Platform
## Project Goal and Software Specification Overview

## 1. Project Summary

This project will create a controlled software platform for implementing, running, and comparing three metaheuristic optimization algorithms:

- **Simulated Annealing (SA)**
- **Tabu Search (TS)**
- **Particle Swarm Optimization (PSO)**

The algorithms will be evaluated across three application domains:

1. **Traveling Salesman Problem (TSP) / Route Optimization**
2. **Machine–Job Scheduling**
3. **Machine-Learning Feature Selection**

The purpose of the project is **not** to identify one algorithm as universally superior.

Instead, the system must determine how the algorithms behave under different problem structures, problem sizes, parameter configurations, and computational constraints. The study will examine the practical trade-offs associated with each algorithm, including:

- Final solution quality
- Convergence speed
- Computational efficiency
- Scalability
- Stability across repeated runs
- Sensitivity to parameter settings
- Difficulty of adaptation and implementation

The software should provide a common experimental environment so that the three algorithms can be compared as fairly and consistently as possible.

---

## 2. Research Goal

The main research question is:

> How do Simulated Annealing, Tabu Search, and Particle Swarm Optimization differ in their effectiveness across route optimization, job scheduling, and machine-learning feature selection in terms of solution quality, convergence speed, scalability, and ease of implementation?

The supporting questions are:

1. How do the algorithms compare on TSP route optimization?
2. How do they compare in machine–job scheduling using makespan?
3. How do they compare in feature selection using predictive performance and feature reduction?
4. How does algorithm performance change as problem size increases?
5. How difficult is each algorithm to adapt, configure, tune, and implement for each problem type?

---

## 3. Core Principle of the Study

The project must use a **controlled comparison framework**.

Previous studies frequently used different:

- Datasets
- Hardware
- Programming languages
- Parameter settings
- Stopping rules
- Computational budgets
- Solution representations
- Statistical methods
- Numbers of repeated trials

These inconsistencies make it difficult to determine whether reported performance differences are caused by the algorithms themselves or by differences in experimental design.

This platform must reduce those inconsistencies by using:

- Shared datasets or benchmark instances
- A common experiment runner
- Clearly documented parameters
- Comparable computational budgets
- Repeated independent runs
- Recorded random seeds
- Standardized result formats
- Consistent statistical reporting
- Common visualization and export tools

---

## 4. Main Users

The expected users are researchers, students, or project members who need to:

- Configure optimization experiments
- Select a problem domain
- Select an algorithm
- Load a benchmark instance or dataset
- Set algorithm parameters
- Run one experiment
- Run repeated trials
- Compare multiple algorithms
- Inspect convergence behavior
- Export raw and summarized results
- Reproduce previous experiments

The system should be understandable to users who know basic optimization concepts but should not require them to edit source code for ordinary experiments.

---

## 5. High-Level System Workflow

The intended workflow is:

1. The user opens the application.
2. The user selects a problem domain:
   - TSP
   - Job scheduling
   - Feature selection
3. The user selects or uploads a benchmark instance or dataset.
4. The user selects one or more algorithms:
   - SA
   - TS
   - PSO
5. The user configures the algorithm parameters.
6. The user selects an experimental budget and stopping rules.
7. The user selects the number of independent runs.
8. The system validates all settings.
9. The experiment runner executes the selected algorithms.
10. The system records:
    - Objective values
    - Best-so-far values
    - Objective evaluations
    - Runtime
    - Convergence history
    - Final solutions
    - Random seeds
    - Parameter settings
11. The system calculates summary statistics.
12. The user views tables, charts, and comparisons.
13. The user exports the complete experiment results.

---

# 6. Problem Domains

## 6.1 Traveling Salesman Problem / Route Optimization

### 6.1.1 Problem Definition

The Traveling Salesman Problem asks for the shortest closed route that:

- Visits every city exactly once
- Returns to the starting city

A candidate solution is represented as a permutation of city identifiers.

Example:

```text
[0, 4, 2, 1, 3]
```

This represents the route:

```text
0 → 4 → 2 → 1 → 3 → 0
```

### 6.1.2 Objective

The main objective is:

```text
Minimize total route distance
```

The objective function must include the distance from the final city back to the starting city.

### 6.1.3 Input Data

The system should support at least one of the following formats:

- City coordinates
- Distance matrix
- Standard benchmark file format, if selected by the research group

Each TSP instance should contain:

- Instance name
- Number of cities
- City identifiers
- Coordinates or distance matrix
- Known optimum, when available
- Source or benchmark reference

### 6.1.4 Required Route Operators

The system should support valid permutation-based moves such as:

- **Swap:** exchange two cities
- **Insertion:** remove one city and insert it elsewhere
- **Inversion:** reverse a section of the route
- **2-opt:** remove two route edges and reconnect the route differently

The exact operators used in the final experiment must be documented.

### 6.1.5 TSP Outputs

For every run, record:

- Best route
- Best route distance
- Initial route distance
- Final route distance
- Known optimum, if available
- Percentage gap from known optimum
- Runtime
- Objective evaluation count
- Convergence history
- Random seed
- Algorithm parameters

---

## 6.2 Machine–Job Scheduling

### 6.2.1 General Problem Definition

The scheduling domain involves deciding:

- Which machine handles each job or operation
- In what order jobs or operations are processed
- How to satisfy the selected scheduling constraints

The primary performance measure identified in the study is **makespan**.

Makespan is the completion time of the final job or operation in the schedule.

### 6.2.2 Objective

The main objective is:

```text
Minimize makespan
```

Possible secondary measures may include:

- Total completion time
- Tardiness
- Machine utilization
- Workload balance

These secondary objectives must not be added to the final implementation unless the research group explicitly approves them.

### 6.2.3 Required Final Scheduling Definition

The uploaded research materials identify machine–job scheduling as a target domain but do not completely fix the exact scheduling formulation.

Before final implementation, the research group must select one precise formulation, such as:

- Job-shop scheduling
- Flow-shop scheduling
- Parallel-machine scheduling
- Flexible job-shop scheduling
- Another explicitly defined machine–job model

The final specification must define:

- Number of machines
- Number of jobs
- Number of operations per job
- Processing times
- Machine eligibility
- Job precedence constraints
- Release times, if used
- Due dates, if used
- Whether machine preemption is allowed
- Whether setup times are included
- Whether all jobs are available at time zero

Cursor must not invent these rules.

### 6.2.4 Candidate Solution Representation

The representation depends on the chosen scheduling formulation.

Possible structures include:

- Job sequence only
- Operation sequence
- Machine assignment vector
- Combined operation-sequence and machine-assignment representation

The final implementation must include a decoder that converts the candidate representation into a valid schedule.

### 6.2.5 Scheduling Outputs

For every run, record:

- Best schedule
- Makespan
- Initial makespan
- Final makespan
- Machine assignment
- Operation sequence
- Start and finish times
- Runtime
- Objective evaluation count
- Convergence history
- Random seed
- Algorithm parameters

A Gantt chart should be generated when the schedule representation supports it.

---

## 6.3 Machine-Learning Feature Selection

### 6.3.1 Problem Definition

Feature selection searches for a subset of input variables that preserves or improves predictive performance while reducing the number of selected features.

A candidate solution is represented as a binary vector.

Example:

```text
[1, 0, 1, 1, 0]
```

This means:

- Feature 1 is selected
- Feature 2 is excluded
- Feature 3 is selected
- Feature 4 is selected
- Feature 5 is excluded

### 6.3.2 Objectives

The feature-selection objective must consider both:

- Predictive performance
- Number or percentage of selected features

A possible weighted objective is:

```text
objective =
    performance_weight × predictive_loss
    + reduction_weight × selected_feature_ratio
```

The exact objective equation and weights remain to be finalized by the research group.

The system should not silently select the weights.

### 6.3.3 Required Experimental Controls

All three algorithms must use the same:

- Dataset
- Preprocessing method
- Missing-value treatment
- Feature scaling
- Categorical encoding
- Classifier
- Train-validation-test split
- Cross-validation procedure
- Predictive metric
- Random seed policy

Feature selection must be performed using only training or validation information.

The test set must be reserved for final evaluation and must not guide the optimization process.

### 6.3.4 Candidate Classifier

The uploaded materials do not specify one final classifier.

Possible choices may include:

- K-Nearest Neighbors
- Logistic Regression
- Support Vector Machine
- Decision Tree
- Another approved classifier

The research group must select the final classifier before implementation is locked.

### 6.3.5 Possible Predictive Metrics

Depending on the dataset and prediction task:

- Accuracy
- F1-score
- Precision
- Recall
- Hamming loss
- Another approved metric

The selected metric must be the same across all three algorithms for a given dataset.

### 6.3.6 Feature-Selection Outputs

For every run, record:

- Selected feature indices
- Selected feature names
- Number of selected features
- Percentage of selected features
- Validation performance
- Final test performance
- Objective value
- Runtime
- Objective evaluation count
- Convergence history
- Random seed
- Algorithm parameters

---

# 7. Algorithms

## 7.1 Simulated Annealing

### 7.1.1 Core Behavior

Simulated Annealing is a stochastic, single-solution search method.

The algorithm:

1. Starts with one candidate solution.
2. Generates a neighboring solution.
3. Accepts the neighbor immediately if it is better.
4. May accept a worse solution based on temperature and deterioration.
5. Gradually decreases the temperature.
6. Becomes more selective as the search continues.

A typical minimization acceptance probability is:

```text
P(accept) = exp(-delta / temperature)
```

where:

```text
delta = new_cost - current_cost
```

If `delta <= 0`, the new solution is accepted.

### 7.1.2 Required Parameters

The configuration must expose:

- Initial temperature
- Final temperature
- Cooling schedule
- Cooling factor
- Moves per temperature
- Maximum objective evaluations
- Maximum runtime, if enabled
- No-improvement stopping threshold
- Neighborhood operator
- Initial-solution method
- Random seed

### 7.1.3 Cooling Schedules

The first version should support at least geometric cooling:

```text
new_temperature = cooling_factor × current_temperature
```

Additional schedules may be added later, but they should not be required for the first implementation unless approved.

### 7.1.4 Domain Adaptations

For TSP:

- Swap
- Insertion
- Inversion
- 2-opt

For scheduling:

- Swap jobs or operations
- Insert an operation
- Change machine assignment
- Other formulation-specific valid moves

For feature selection:

- Add a feature
- Remove a feature
- Flip one binary decision
- Swap one selected and one unselected feature

### 7.1.5 Important Risk

SA is sensitive to:

- Temperature scale
- Cooling rate
- Objective-value scale
- Number of moves
- Stopping condition

All values must be recorded for reproducibility.

---

## 7.2 Tabu Search

### 7.2.1 Core Behavior

Tabu Search is a single-solution, memory-guided search method.

The algorithm:

1. Starts with one candidate solution.
2. Generates a set of neighboring candidates.
3. Evaluates admissible candidates.
4. Selects the best admissible move, even if it worsens the current solution.
5. Records recent moves or attributes in a tabu structure.
6. Temporarily prevents recently used moves from being reversed.
7. Applies an aspiration rule when a tabu move is exceptionally good.

### 7.2.2 Required Parameters

The configuration must expose:

- Tabu tenure
- Neighborhood operator
- Candidate-list size
- Aspiration criterion
- Tabu representation
- Maximum objective evaluations
- Maximum runtime, if enabled
- Maximum iterations
- No-improvement stopping threshold
- Initial-solution method
- Random seed

### 7.2.3 Aspiration Criterion

The default aspiration rule should allow a tabu move when it produces a solution better than the best solution found so far.

### 7.2.4 Domain Adaptations

For TSP, the tabu list may store:

- Swapped city pair
- Removed or added route edges
- Reversed segment
- Move signature

For scheduling, it may store:

- Swapped jobs
- Moved operation
- Machine reassignment
- Position change

For feature selection, it may store:

- Added feature
- Removed feature
- Flipped feature index
- Feature swap

### 7.2.5 Important Risk

TS performance depends strongly on:

- Neighborhood quality
- Candidate-list size
- Tabu tenure
- Aspiration rule
- Meaning of a tabu attribute

The software must make these definitions explicit and save them with every run.

---

## 7.3 Particle Swarm Optimization

### 7.3.1 Core Behavior

Particle Swarm Optimization is a population-based search method.

Each particle maintains:

- Current position
- Current objective value
- Personal-best position
- Personal-best objective value

The swarm maintains:

- Global-best or neighborhood-best position
- Global-best or neighborhood-best objective value

Standard continuous PSO uses:

```text
velocity =
    inertia × previous_velocity
    + cognitive_coefficient × random_1 × (personal_best - position)
    + social_coefficient × random_2 × (global_best - position)

position = position + velocity
```

However, the three project domains are discrete.

Therefore, the system must use approved discrete variants or decoding mechanisms.

### 7.3.2 Required Parameters

The configuration must expose:

- Swarm size
- Inertia weight
- Cognitive coefficient
- Social coefficient
- Topology
- Velocity or movement control
- Maximum objective evaluations
- Maximum runtime, if enabled
- Maximum generations
- No-improvement stopping threshold
- Initialization method
- Random seed

### 7.3.3 Domain Adaptations

For feature selection:

- Binary PSO
- Probability or sigmoid-based decoding
- Threshold-based feature selection

For TSP:

- Permutation-based PSO
- Swap-sequence movement
- Crossover-based movement
- Route decoder
- Optional 2-opt refinement, only if approved

For scheduling:

- Discrete or geometric PSO
- Operation-sequence update
- Machine-assignment update
- Crossover or decoder-based movement

### 7.3.4 Important Risk

PSO may converge prematurely when:

- Particles follow one leader too early
- Population diversity is lost
- Social influence is too strong
- Discrete encoding collapses many particles into similar solutions

The system should record diversity-related information when practical, but this is optional unless required by the final methodology.

---

# 8. Fair Experimental Comparison

## 8.1 Why Equal Iterations Are Not Fair

The algorithms perform different amounts of work per iteration:

- One SA transition may evaluate one neighbor.
- One TS iteration may evaluate many candidate neighbors.
- One PSO generation evaluates the entire swarm.

Therefore, the primary comparison should not rely only on equal iteration counts.

## 8.2 Primary Budget

The preferred primary computational budget is:

```text
Maximum number of objective-function evaluations
```

Every call to a domain objective function must increment an evaluation counter.

The experiment runner must stop the algorithm when the evaluation budget is exhausted.

## 8.3 Secondary Budget

The platform should also record:

- Wall-clock runtime
- Number of iterations or generations
- Number of accepted moves
- Number of improving moves
- Number of non-improving moves, when relevant

A runtime limit may be supported as an optional stopping condition.

## 8.4 Shared Conditions

For a valid comparison, all selected algorithms should use:

- The same problem instance
- The same objective definition
- The same evaluation budget
- The same hardware environment
- The same implementation language
- The same result-recording method
- Comparable initialization rules
- The same number of repeated runs

The system should store machine and software information where practical.

---

# 9. Repeated Runs and Random Seeds

Metaheuristic algorithms are stochastic or may contain stochastic components.

A single run is not sufficient.

The experiment system must support:

- A configurable number of independent runs
- A base seed
- A generated list of run seeds
- Reusing the same seed list across algorithms
- Saving every run seed in the output

Example:

```text
Base seed: 1000
Run seeds: 1000, 1001, 1002, 1003, ...
```

The final number of required runs remains to be approved by the research group.

A reasonable configurable default may be provided, but the software must not present it as a final research decision.

---

# 10. Metrics

## 10.1 Common Metrics

Every algorithm-domain run should record:

- Final objective value
- Best objective value
- Initial objective value
- Runtime
- Objective evaluation count
- Iteration or generation count
- Best-so-far convergence history
- Final solution
- Best solution
- Random seed
- Parameter configuration
- Stop reason
- Success or failure status

## 10.2 Solution Quality

### TSP

- Route distance
- Gap from known optimum
- Best route

Possible gap calculation:

```text
gap_percentage =
    ((obtained_distance - known_optimum) / known_optimum) × 100
```

### Scheduling

- Makespan
- Gap from known lower bound or optimum, when available
- Schedule validity

### Feature Selection

- Validation performance
- Final test performance
- Number of selected features
- Percentage reduction
- Combined objective value

## 10.3 Convergence

Convergence data should store:

```text
objective_evaluations, best_objective_value
```

Optional additional fields:

- Current objective value
- Temperature
- Tabu-list status
- Swarm diversity
- Accepted move
- Improvement flag

Convergence should be plotted against:

- Objective evaluations
- Runtime
- Iteration or generation count

The primary plot should use objective evaluations.

## 10.4 Scalability

Scalability should be evaluated by increasing problem size.

Examples:

### TSP

- Small number of cities
- Medium number of cities
- Large number of cities

### Scheduling

- Increasing numbers of jobs
- Increasing numbers of machines
- Increasing numbers of operations

### Feature Selection

- Increasing numbers of features
- Increasing numbers of samples
- Datasets with different dimensionality

The exact benchmark sizes remain to be finalized.

## 10.5 Stability

Across repeated runs, calculate:

- Mean
- Standard deviation
- Median
- Minimum
- Maximum
- Best result
- Worst result
- Interquartile range
- Success frequency, when applicable

---

# 11. Statistical Analysis

The platform should provide data suitable for statistical testing.

Possible tests include:

- Paired t-test
- Wilcoxon signed-rank test
- Analysis of variance
- Friedman test
- Post-hoc pairwise comparison
- Tukey HSD, when assumptions are met

The final test selection must be determined by the research methodology and data assumptions.

The software may provide automated summaries, but it should not automatically claim statistical significance without:

- An approved test
- Appropriate assumptions
- Multiple observations
- A defined significance level
- Correction for multiple comparisons when required

The system should export analysis-ready CSV files so the statistical analysis can also be performed separately.

---

# 12. Parameter Configuration

## 12.1 Configuration Storage

Every experiment configuration must be saved in a machine-readable format such as JSON.

Example:

```json
{
  "experiment_name": "tsp_medium_comparison",
  "domain": "tsp",
  "instance": "example_100",
  "algorithms": ["sa", "ts", "pso"],
  "runs": 30,
  "evaluation_budget": 100000,
  "seed_policy": {
    "base_seed": 1000
  }
}
```

Each algorithm should have its own parameter object.

## 12.2 Parameter Validation

The system must reject invalid parameter values.

Examples:

- Cooling factor must be between 0 and 1 for geometric cooling.
- Initial temperature must be positive.
- Final temperature must be lower than the initial temperature.
- Tabu tenure must be a positive integer.
- Candidate-list size must be positive.
- Swarm size must be at least 2.
- Feature-selection solutions must select at least one feature unless empty subsets are explicitly allowed.
- TSP routes must contain every city exactly once.
- Scheduling solutions must satisfy the selected scheduling rules.

## 12.3 Parameter Presets

The system may provide:

- Default preset
- Small-budget preset
- Standard comparison preset
- Large-budget preset

Presets must be labeled as software conveniences, not as final research-optimal settings.

---

# 13. Proposed Software Architecture

## 13.1 Main Modules

The project should be divided into the following modules:

```text
src/
├── algorithms/
├── domains/
├── experiments/
├── metrics/
├── statistics/
├── visualization/
├── storage/
├── ui/
├── config/
└── utilities/
```

## 13.2 Algorithms Module

Possible structure:

```text
algorithms/
├── base.py
├── simulated_annealing.py
├── tabu_search.py
└── particle_swarm.py
```

All algorithms should follow a common interface.

Example conceptual interface:

```python
class OptimizationAlgorithm:
    def initialize(self, problem, config, seed):
        ...

    def run(self):
        ...

    def step(self):
        ...

    def get_best_solution(self):
        ...

    def get_best_objective(self):
        ...

    def get_history(self):
        ...
```

## 13.3 Domains Module

Possible structure:

```text
domains/
├── base_problem.py
├── tsp/
├── scheduling/
└── feature_selection/
```

Each problem domain should define:

- Solution representation
- Initial-solution generation
- Objective evaluation
- Validity checking
- Repair, if approved
- Neighborhood generation
- PSO-compatible movement or decoding
- Domain-specific metrics
- Output serialization

Example conceptual interface:

```python
class OptimizationProblem:
    def create_initial_solution(self, rng):
        ...

    def evaluate(self, solution):
        ...

    def is_valid(self, solution):
        ...

    def repair(self, solution):
        ...

    def serialize_solution(self, solution):
        ...
```

## 13.4 Experiment Module

The experiment module should handle:

- Experiment configuration
- Seed generation
- Repeated runs
- Budget enforcement
- Progress reporting
- Cancellation
- Error isolation
- Result aggregation
- Output directory creation

Possible structure:

```text
experiments/
├── runner.py
├── budget.py
├── seed_manager.py
├── run_context.py
└── batch_runner.py
```

## 13.5 Metrics Module

The metrics module should calculate:

- Common run metrics
- TSP metrics
- Scheduling metrics
- Feature-selection metrics
- Convergence summaries
- Stability statistics

## 13.6 Statistics Module

The statistics module should contain:

- Descriptive statistics
- Assumption checks
- Approved inferential tests
- Pairwise comparisons
- Effect sizes
- Result formatting

## 13.7 Visualization Module

The visualization module should generate:

- Convergence curves
- Runtime comparisons
- Box plots
- Scalability plots
- TSP route visualizations
- Scheduling Gantt charts
- Feature-selection frequency charts
- Summary tables

## 13.8 Storage Module

The storage module should handle:

- JSON configuration files
- CSV run results
- JSON detailed results
- Convergence-history files
- Generated charts
- Logs
- Experiment metadata

---

# 14. Suggested Output Folder Structure

Each experiment should create a self-contained output folder.

Example:

```text
results/
└── 2026-08-03_070000_tsp_comparison/
    ├── experiment_config.json
    ├── environment.json
    ├── seeds.csv
    ├── runs.csv
    ├── summary.csv
    ├── statistics.csv
    ├── convergence/
    │   ├── sa_run_001.csv
    │   ├── ts_run_001.csv
    │   └── pso_run_001.csv
    ├── solutions/
    │   ├── sa_run_001.json
    │   ├── ts_run_001.json
    │   └── pso_run_001.json
    ├── charts/
    │   ├── convergence.png
    │   ├── objective_boxplot.png
    │   └── runtime_comparison.png
    └── logs/
        └── experiment.log
```

---

# 15. Data Models

## 15.1 Experiment Configuration

An experiment configuration should contain:

- Experiment ID
- Experiment name
- Creation time
- Domain
- Dataset or benchmark
- Problem size
- Selected algorithms
- Number of runs
- Evaluation budget
- Runtime budget
- Seed list
- Domain configuration
- Algorithm configurations
- Output settings

## 15.2 Single Run Result

A single run result should contain:

```json
{
  "experiment_id": "exp_001",
  "run_id": "sa_run_001",
  "algorithm": "simulated_annealing",
  "domain": "tsp",
  "instance": "example_100",
  "seed": 1000,
  "status": "completed",
  "stop_reason": "evaluation_budget",
  "initial_objective": 25000.0,
  "best_objective": 12000.0,
  "final_objective": 12100.0,
  "runtime_seconds": 12.4,
  "objective_evaluations": 100000,
  "iterations": 100000,
  "parameters": {},
  "best_solution_path": "solutions/sa_run_001.json",
  "convergence_path": "convergence/sa_run_001.csv"
}
```

## 15.3 Summary Result

The summary should group results by:

- Domain
- Instance
- Problem size
- Algorithm
- Parameter configuration

Summary fields should include:

- Number of successful runs
- Mean objective
- Standard deviation
- Median
- Minimum
- Maximum
- Mean runtime
- Mean evaluation count
- Success frequency
- Mean gap from optimum, when available

---

# 16. User Interface Requirements

The exact interface type has not yet been finalized.

Possible options include:

- Web application
- Desktop application
- Local dashboard
- Command-line interface with generated reports

A web or local dashboard is recommended for ease of comparison, but Cursor should not select a framework until the technology stack is approved.

## 16.1 Main Screens

The application should contain:

### Dashboard

- Recent experiments
- Experiment status
- Quick summaries
- Links to results

### New Experiment

- Domain selection
- Dataset selection
- Algorithm selection
- Parameter forms
- Budget settings
- Run count
- Seed settings
- Validation messages
- Start button

### Running Experiment

- Progress bar
- Current algorithm
- Current run
- Evaluation count
- Runtime
- Current best result
- Cancel button
- Live convergence chart, if practical

### Results

- Summary table
- Algorithm ranking by selected metric
- Convergence charts
- Runtime charts
- Stability plots
- Domain-specific visualization
- Parameter details
- Export controls

### Experiment History

- Search
- Filter by domain
- Filter by algorithm
- Reopen results
- Duplicate configuration
- Delete experiment, with confirmation

---

# 17. Logging and Error Handling

The system must log:

- Experiment start
- Experiment end
- Configuration
- Dataset loaded
- Algorithm initialization
- Run start and end
- Seed
- Budget exhaustion
- Validation errors
- Exceptions
- Cancelled runs
- Export operations

A failed run should not automatically destroy the entire batch.

The system should:

- Mark the failed run
- Save the error message
- Continue other runs when safe
- Include failure counts in the summary

---

# 18. Reproducibility Requirements

Every completed experiment must save enough information to reproduce it.

Required information includes:

- Source code version or commit hash, if available
- Date and time
- Operating system
- Programming-language version
- Dependency versions
- Hardware information, where practical
- Dataset version
- Dataset hash, where practical
- Algorithm parameters
- Domain parameters
- Random seeds
- Evaluation budget
- Runtime budget
- Stopping conditions
- Number of runs
- Objective definition
- Metric definitions

The system should support rerunning an experiment from its saved JSON configuration.

---

# 19. Validation Requirements

## 19.1 General Validation

Before running an experiment:

- Dataset must exist.
- Domain must be selected.
- At least one algorithm must be selected.
- Run count must be positive.
- Evaluation budget must be positive.
- Parameter values must pass validation.
- Output directory must be writable.

## 19.2 TSP Validation

- Every city appears exactly once.
- No city identifier is duplicated.
- Route length matches the number of cities.
- Distance matrix dimensions are valid.
- Distance values are valid.
- Return edge is included in evaluation.

## 19.3 Scheduling Validation

The final checks depend on the chosen scheduling formulation.

At minimum:

- Every required job or operation appears.
- No operation is duplicated.
- Required precedence constraints are satisfied.
- Machine assignments are valid.
- Operations assigned to the same machine do not overlap.
- Makespan is calculated correctly.

## 19.4 Feature-Selection Validation

- Binary vector length matches feature count.
- Selected indices are valid.
- At least one feature is selected unless explicitly allowed otherwise.
- Preprocessing is fit only on training data.
- Test data is not used during optimization.
- The classifier can train on the selected subset.

---

# 20. Testing Requirements

## 20.1 Unit Tests

Tests should cover:

- Objective functions
- Solution validity checks
- Neighborhood operators
- SA acceptance logic
- Temperature updates
- TS tabu-list behavior
- TS aspiration behavior
- PSO update or decoding logic
- Evaluation-budget counting
- Seed reproducibility
- Result serialization
- Summary-statistic calculation

## 20.2 Integration Tests

Integration tests should verify:

- Every algorithm runs on every supported domain.
- Repeated runs produce valid output.
- Saved configurations can be rerun.
- Evaluation budgets are enforced.
- Results are exported correctly.
- Invalid settings are rejected.

## 20.3 Reproducibility Tests

Running the same:

- Algorithm
- Domain
- Dataset
- Parameters
- Seed

should produce the same result unless an external library introduces nondeterminism.

## 20.4 Small Known Cases

Use very small instances with known or exactly computable solutions.

Examples:

- Small TSP instance
- Small scheduling instance
- Small synthetic feature-selection dataset

These cases should confirm that:

- Objective functions are correct.
- Solutions are valid.
- Algorithms can reach reasonable results.
- Known optimum gaps are calculated correctly.

---

# 21. Implementation Complexity

The research question includes ease of implementation.

This concept must be defined carefully.

Possible measurements include:

- Lines of algorithm-specific code
- Number of required parameters
- Number of domain-specific operators
- Number of domain-specific adaptations
- Development time
- Number of validation rules
- Number of algorithm-specific bugs
- Manual difficulty rating

The uploaded materials do not finalize how implementation complexity will be measured.

The research group must select an explicit method.

Cursor should not calculate a subjective implementation score without an approved rubric.

---

# 22. Scope Boundaries

## 22.1 Included in the Initial Scope

- Canonical or clearly defined versions of SA, TS, and PSO
- TSP optimization
- One finalized scheduling formulation
- Feature selection
- Configurable parameters
- Objective-evaluation budgets
- Repeated trials
- Convergence recording
- Descriptive statistics
- Visual comparisons
- Exportable results
- Reproducible experiment configurations

## 22.2 Not Automatically Included

The following should not be added unless explicitly approved:

- Genetic Algorithms
- Ant Colony Optimization
- Differential Evolution
- Artificial Bee Colony
- Deep-learning classifiers
- Cloud deployment
- Real-time logistics data
- Multi-user accounts
- Distributed execution
- Hybrid SA–TS–PSO algorithms
- Automatic hyperparameter optimization
- Multi-objective Pareto-front analysis
- Dynamic scheduling
- Real-time route changes

These may be considered future extensions.

---

# 23. Important Research Risks

## 23.1 Unfair Computational Budgets

Equal iterations can favor one algorithm because the amount of work per iteration differs.

Mitigation:

- Use objective evaluations as the main budget.
- Record runtime.
- Report iteration counts only as secondary information.

## 23.2 Parameter Bias

One algorithm may receive much more tuning than another.

Mitigation:

- Use a documented tuning protocol.
- Separate tuning instances from final test instances.
- Apply comparable tuning effort.

## 23.3 Data Leakage

Feature selection may accidentally use the test set during optimization.

Mitigation:

- Reserve the test set for final evaluation.
- Perform preprocessing inside the approved training workflow.
- Never use final test performance as the optimization objective.

## 23.4 Invalid Discrete PSO

A continuous PSO update may generate invalid routes, schedules, or subsets.

Mitigation:

- Use domain-specific discrete encodings.
- Validate every decoded solution.
- Use repair only when clearly defined and documented.

## 23.5 Overuse of Hybrid Operators

Adding local search, mutation, crossover, or repair may make the algorithm stronger but may obscure whether improvements come from the core method.

Mitigation:

- Begin with clearly documented canonical or minimally adapted algorithms.
- Label all additional operators.
- Avoid comparing a heavily hybridized algorithm against basic versions without explanation.

## 23.6 Insufficient Repeated Runs

One unusually successful run may distort conclusions.

Mitigation:

- Use multiple independent runs.
- Report variation, not only the best result.

---

# 24. Decisions Still Required

The following items are not fully settled in the uploaded materials and must be finalized before Cursor receives a complete build instruction.

## 24.1 Technology

- Programming language
- Backend framework
- User-interface framework
- Database or file-only storage
- Packaging method
- Target operating system

## 24.2 TSP

- Benchmark datasets
- Instance sizes
- File format
- Known-optimum source
- Final move operators
- Whether 2-opt is treated as a normal operator or hybrid local search

## 24.3 Scheduling

- Exact scheduling formulation
- Benchmark dataset
- Constraints
- Solution representation
- Decoder
- Neighborhood operators
- PSO adaptation

## 24.4 Feature Selection

- Datasets
- Classifier
- Predictive metric
- Preprocessing method
- Data-splitting method
- Cross-validation method
- Objective equation
- Performance and reduction weights
- Empty-subset policy

## 24.5 Experimental Design

- Number of repeated runs
- Evaluation budgets
- Problem-size levels
- Parameter-tuning protocol
- Default parameter values
- Statistical tests
- Significance level
- Multiple-comparison correction
- Success definition
- Implementation-complexity rubric

---

# 25. Recommended Development Phases

## Phase 1 — Core Framework

Build:

- Base algorithm interface
- Base problem interface
- Evaluation counter
- Budget controller
- Seed manager
- Run-result model
- Configuration loader
- Logging

## Phase 2 — TSP

Implement:

- TSP loader
- Route evaluator
- Route validation
- TSP neighborhoods
- SA for TSP
- TS for TSP
- Discrete PSO for TSP
- Route visualization
- TSP tests

## Phase 3 — Scheduling

After the exact scheduling model is approved, implement:

- Dataset loader
- Schedule representation
- Decoder
- Makespan evaluator
- Validity checker
- Neighborhoods
- SA, TS, and PSO adaptations
- Gantt chart
- Scheduling tests

## Phase 4 — Feature Selection

After the ML design is approved, implement:

- Dataset loader
- Preprocessing pipeline
- Data splitting
- Classifier wrapper
- Feature-subset evaluator
- Binary representation
- SA, TS, and binary PSO
- Leakage tests
- Feature-selection charts

## Phase 5 — Experiment Runner

Implement:

- Batch execution
- Repeated runs
- Shared seed list
- Evaluation budgets
- Progress tracking
- Cancellation
- Failure isolation
- Result aggregation

## Phase 6 — Analysis and Visualization

Implement:

- Descriptive statistics
- Convergence plots
- Runtime plots
- Box plots
- Scalability plots
- Domain visualizations
- CSV and JSON exports

## Phase 7 — User Interface

Implement:

- New experiment form
- Parameter editor
- Progress screen
- Results dashboard
- Experiment history
- Export controls

## Phase 8 — Validation

Complete:

- Unit tests
- Integration tests
- Reproducibility tests
- Known-case tests
- Documentation
- Example configurations

---

# 26. Definition of Done

The initial system is complete when:

1. SA, TS, and PSO can run successfully on all three finalized domains.
2. Every run uses a recorded random seed.
3. Every objective call is counted.
4. A shared objective-evaluation budget can be enforced.
5. Multiple independent runs can be executed automatically.
6. Every run saves configuration, metrics, convergence history, and solution data.
7. The system produces summary statistics.
8. The system generates comparison charts.
9. The system validates domain-specific solutions.
10. Feature selection avoids test-set leakage.
11. Saved experiments can be reproduced.
12. Invalid configurations produce clear errors.
13. Small known test cases pass.
14. Results can be exported as CSV and JSON.
15. All important assumptions and parameter settings are documented.

---

# 27. Final Instruction for Cursor

Cursor should treat this document as the project overview and high-level specification.

It must not silently invent unresolved research choices.

When a required decision is marked as unresolved, Cursor should either:

1. Leave a clearly marked configuration placeholder,
2. Implement an interface that allows the decision to be supplied later, or
3. Ask for the missing decision before implementing research-dependent behavior.

The implementation must prioritize:

- Fairness
- Reproducibility
- Modularity
- Explicit configuration
- Valid solutions
- Comparable metrics
- Clear experiment records

The central purpose of the software is to support a defensible, controlled comparison of Simulated Annealing, Tabu Search, and Particle Swarm Optimization across route optimization, machine–job scheduling, and machine-learning feature selection.
