# Comparative Evaluation of Simulated Annealing, Tabu Search, and Particle Swarm Optimization Across Practical Optimization Problems

**Version:** v2.2 (2026-08-07)  
**Authors:** Juan Miguel Miranda, Julian Johan Briones, Lance Xavier Lim  
**Emails:** juan_miranda@dlsu.edu.ph, Julian_briones@dlsu.edu.ph, lance_xavier_lim@dlsu.edu.ph  
**Status:** Full sample tests complete — TSP 18/18, JSP 15/15, FS 12/12 (45/45 comparison cells)

---

## ABSTRACT

This study compares Simulated Annealing (SA), Tabu Search (TS), and Particle Swarm Optimization (PSO) across route optimization, job scheduling, and machine-learning feature selection. The work merges a structured literature review and formal search-theoretic analysis with controlled sample tests on a shared experimental platform. Tests use equal objective-evaluation budgets, disjoint tuning and comparison instance sets, literature-informed parameter grids, and 30 independent seeds per algorithm per benchmark.

On Traveling Salesman Problem (TSP) instances (51–195 cities), TS achieved the lowest best-of-30 gap to known optima on every instance (0.33–17.6% on reported instances), followed by SA (8–19% best-gap range on held-out instances); reported PSO gaps (58–264%) are **not treated as valid standalone PSO evidence** because the implementation does not apply the configured nearest-neighbor initializer to the swarm (§3.5, §5.1). On job-shop scheduling (JSP)—the cleanest protocol block with disjoint tuning/comparison sets and a documented shared initializer—TS led on all five held-out benchmarks (1.8–21.1% best gap); PSO beat SA on **all five** instances but remained behind TS. On feature selection, the three algorithms produced similar wrapper-objective scores (~0.01–0.05 spread), but the objective uses raw (non-standardized) features and α=0.9/β=0.1 weights; PSO matched TS at best-seed on three of four EW datasets while TS had the lowest mean on two of four (BreastEW, WineEW).

Early pilot tests (10 runs, single instances, 20k evaluations) had shown SA ahead on one 50-city TSP after a cooling-schedule correction; the expanded protocol consistently ranked TS first on routing, confirming that TS advantage is scale- and budget-dependent rather than universal. The study does not identify a single winner. It delivers a Comparative Evaluation Framework linking algorithm choice to problem representation, evaluation cost, and search mechanism. Rankings align with reviewed literature expectations even where absolute gap magnitudes differ because of benchmark scale, initializer design, and standalone (non-hybrid) implementations.

**Keywords:** Simulated Annealing, Tabu Search, Particle Swarm Optimization, route optimization, job scheduling, feature selection, metaheuristics, comparative evaluation.

---

## 1. INTRODUCTION

Optimization problems in route planning, production scheduling, and machine-learning preprocessing involve search spaces too large for exhaustive enumeration. Metaheuristics balance exploration and exploitation without guaranteeing global optimality. This study focuses on SA, TS, and PSO because they represent three distinct search philosophies: probabilistic single-solution search (SA), memory-guided neighborhood search (TS), and cooperative population-based search (PSO).

The No Free Lunch principle indicates that no algorithm is universally superior; performance depends on problem structure, representation, parameters, and computational budget (Wolpert & Macready, 1997; Talbi, 2009).

### 1.1 Main Research Question

How do Simulated Annealing, Tabu Search, and Particle Swarm Optimization differ in their effectiveness across route optimization, job scheduling, and machine-learning feature selection?

### 1.2 Supporting Research Questions

1. **TSP** — route quality, convergence, efficiency, scalability  
2. **JSP** — schedule quality (makespan), efficiency, convergence, scalability  
3. **FS** — predictive performance, feature reduction, cost, stability  
4. Implementation requirements, parameter sensitivity, strengths, limitations  
5. Alignment of sample-test outcomes with numeric patterns and stated mechanisms in the reviewed literature  

### 1.3 Study Scope and Deliverable

The deliverable is a **Comparative Evaluation Framework** combining literature synthesis with sample-test evidence. Sample tests demonstrate behavior under a fixed, equal-effort protocol; they are not industrial-scale benchmarks. RQ5 emphasizes **directional alignment and mechanistic consistency** rather than point equality of gap percentages across unrelated studies.

---

## 2. REVIEW OF RELATED LITERATURE

### 2.1 Metaheuristic Optimization

Optimization refers to the process of identifying the best feasible solution from a set of alternatives subject to defined objectives and constraints. Many real-world problems, including route planning, job scheduling, and machine-learning feature selection, become increasingly difficult as the number of possible solutions grows. Although exact algorithms can guarantee optimality, their computational requirements may become impractical for large and complex problem instances. Researchers therefore commonly use heuristic and metaheuristic methods to obtain high-quality solutions within reasonable computational limits.

Heuristics are methods designed for specific problems, while metaheuristics are more general search methods that can be adapted to different problems. They do not guarantee the best possible answer, but they try to find good solutions without checking every possibility. Their usefulness is especially apparent in combinatorial problems, where the number of feasible configurations may increase exponentially or factorially as the problem becomes larger.

A central concern in metaheuristic design is the balance between exploration and exploitation. Exploration involves examining new or less-visited regions of the solution space, while exploitation involves refining solutions in areas already known to be promising. Too much exploitation can trap the algorithm in a local optimum, while too much exploration can waste time checking weak solutions. Effective metaheuristics try to balance both (Youssef et al., 2001).

Metaheuristic algorithms may generally be classified as either single-solution or population-based methods (Talbi, 2009). Single-solution methods maintain one current candidate and repeatedly move to a neighboring solution. Simulated Annealing and Tabu Search belong to this category, although they use substantially different mechanisms for escaping local optima. Simulated Annealing relies on temperature-dependent probabilistic acceptance, whereas Tabu Search uses adaptive memory and temporary restrictions on recently performed moves. Population-based methods maintain several candidate solutions simultaneously. Particle Swarm Optimization is a population-based method in which particles exchange information through personal and collective experience. This population structure allows PSO to examine several areas of the solution space during the same search. However, rapid information sharing may also cause the particles to converge prematurely when the population follows an inferior leader too quickly (Kennedy & Eberhart, 1995; Sengupta et al., 2019).

The No Free Lunch principle indicates that no optimization algorithm can be universally superior across every possible problem. An algorithm that performs strongly for one problem category may perform poorly for another. An algorithm's performance depends on the problem, how solutions are represented, its parameter settings, and the available computational budget. Results from one application should therefore not be treated as proof that the same algorithm will perform best everywhere. Simulated Annealing, Tabu Search, and Particle Swarm Optimization were selected for the present study because they represent three substantially different search strategies. Simulated Annealing represents probabilistic single-solution search, Tabu Search represents memory-guided neighborhood search, and Particle Swarm Optimization represents cooperative population-based search. Comparing them across several problem types may provide a clearer understanding of the conditions under which each method performs effectively.

### 2.2 Simulated Annealing

Simulated Annealing is a single-solution metaheuristic introduced by Kirkpatrick et al. (1983). It is inspired by the process of heating and slowly cooling material. In optimization, temperature controls how willing the algorithm is to accept worse solutions while searching for a better one. The algorithm begins with an initial candidate solution and generates a neighboring solution through a problem-specific modification. If the neighbor improves the objective value, it is accepted immediately. A worse neighbor may also be accepted according to a probability determined by the size of the deterioration and the current temperature. A common expression for this rule is: acceptance probability = exp(−cost increase / temperature). When temperature is high, even some substantially worse solutions may be accepted. This helps the algorithm escape local optima. As the temperature decreases, it becomes less willing to accept worse solutions and focuses more on improving the current result. Unlike ordinary hill climbing, which accepts only better moves, Simulated Annealing may temporarily accept worse ones. This can help it escape a local optimum and reach a better solution later.

The cooling schedule is one of the most important parts of Simulated Annealing. It controls how quickly the temperature decreases and therefore how quickly the algorithm shifts from exploration to refinement. A common geometric schedule uses: new temperature = cooling factor × current temperature. A cooling factor close to one produces slower cooling and prolonged exploration, while a smaller factor causes more rapid cooling and earlier exploitation. Cooling too quickly may cause premature convergence because the algorithm loses its ability to escape local optima before enough of the solution space has been explored. Cooling too slowly may improve exploration but can require excessive computation. The appropriate balance depends on the structure of the problem, the cost scale, and the neighborhood operator.

Youssef et al. (2001) demonstrated that the numerical scale of the objective function can significantly affect Simulated Annealing. In their VLSI floorplanning experiment, Youssef et al. found that the scale of the objective values caused SA to accept too many poor moves. After adjusting the scale, its performance improved substantially. Their findings show that temperature values cannot be selected independently of the objective-function scale. An apparently poor Simulated Annealing result may therefore reflect inadequate calibration rather than an inherent weakness of the method.

Several studies have proposed adaptive cooling methods to reduce parameter sensitivity. Zhan et al. (2016) developed List-Based Simulated Annealing for the Traveling Salesman Problem. Instead of using one fixed cooling schedule, the method adjusted its temperature based on the search behavior. This allowed faster cooling early in the search and slower cooling during later refinement. The list-based approach reduced dependence on a fixed initial temperature and cooling coefficient. Zhan et al. reported competitive results on TSP instances ranging from 48 to 85,900 cities. Their experiments also examined several neighborhood operators. Inversion was the strongest individual operator, insertion generally performed second, and simple swapping performed worst. A hybrid neighborhood that combined inversion, insertion, and swapping produced the strongest overall results. These findings demonstrate that Simulated Annealing performance depends not only on cooling but also on the quality of the neighborhood moves.

Hybrid methods have also incorporated Simulated Annealing into population-based algorithms. Mhamdi et al. (2011) combined Particle Swarm Optimization, Simulated Annealing, and Tabu Search for microwave-image reconstruction. Particle Swarm Optimization provided population-level movement, while Simulated Annealing and Tabu Search locally improved different portions of the swarm. The complete three-algorithm hybrid produced lower reconstruction error than standard PSO and the two partial hybrids. The authors attributed the improvement to the combination of global exploration, probabilistic escape, and memory-guided local refinement.

Simulated Annealing has several important advantages. Its basic structure is conceptually simple, it does not require gradient information, and it can be adapted to continuous, nonlinear, discontinuous, and combinatorial objective functions. Its acceptance of worsening moves gives it a direct mechanism for leaving local optima. The neighborhood operator can also be designed according to the structure of the problem, allowing the method to be applied to route optimization, scheduling, VLSI design, network-flow parameter tuning, feature selection, and inverse reconstruction.

However, Simulated Annealing also has important limitations. Its effectiveness is sensitive to the starting temperature, cooling rate, number of transitions, objective-function scale, and stopping rule. Poorly selected parameters may cause premature convergence or excessively long search. Because the method has no explicit memory of previously explored solutions, it may revisit similar regions or spend substantial computation on low-quality candidates. Its stochastic nature also creates variability across runs, making repeated independent trials necessary when assessing its performance.

### 2.3 Tabu Search

Tabu Search is a memory-based metaheuristic developed by Glover (1989). It can accept moves that do not immediately improve the solution and uses its search history to avoid repeatedly returning to the same choices. A basic Tabu Search procedure begins with an initial solution, generates a set of neighboring candidates, and selects the best admissible neighbor. The selected neighbor does not need to improve the current solution. By accepting the best available nonimproving move, the algorithm can move away from a local optimum and continue exploring the solution space.

Unlike Simulated Annealing, Tabu Search does not rely mainly on probabilistic acceptance. It uses a tabu list to restrict recently performed moves or recently encountered solution attributes. When a move is performed, its reversal or selected characteristics are prohibited for a limited number of iterations. These restrictions prevent the search from immediately undoing its decisions and repeatedly cycling among the same solutions. The amount of time a move remains restricted is known as tabu tenure. If the tabu tenure is too short, the search may repeat itself. If it is too long, useful moves may be blocked. The best setting depends on the problem.

Watson et al. (2005) analyzed the behavior of Tabu Search on the Job-Shop Scheduling Problem and found that increasing tabu tenure expanded the effective region explored by the search. Larger tenure values substantially increased solution time because the search was forced farther from previously visited areas. The authors recommended selecting the smallest tenure that still prevents cycling and stagnation. Their findings show that stronger restrictions do not automatically produce better search performance. Tabu restrictions may occasionally prevent an exceptionally strong move.

An aspiration criterion allows a tabu move when it satisfies a sufficiently desirable condition. The most common aspiration rule permits a tabu move when it produces a solution better than the best solution found during the search. This prevents memory restrictions from blocking a new global best candidate. Tabu Search may incorporate several levels of adaptive memory. Short-term memory prevents cycling by recording recently used moves or attributes. Intermediate-term memory supports intensification by identifying features that frequently appear in high-quality solutions. Long-term memory supports diversification by recording how often particular decisions have been selected. Frequently used features may be penalized so that the algorithm is encouraged to examine less-visited areas. Glover (1989) also described more advanced uses of memory that allow Tabu Search to explore areas that ordinary local search may avoid. This shows that Tabu Search is more than simply a list of forbidden moves.

Watson et al. (2005) studied how Tabu Search behaves in job-shop scheduling. They found that the search often stays close to local optima but can move away from one and continue toward another promising solution. The study also found that problem difficulty was strongly related to the effective width of the region explored rather than the total number of feasible schedules. The initial solution had limited influence on difficult instances unless it began extremely close to an optimum. This suggests that the search dynamics and memory structures may become more important than starting quality as the problem becomes harder.

Tabu Search has been widely applied to discrete problems such as scheduling, routing, feature selection, and production planning. Its explicit memory helps prevent short-term repetition, while best-admissible movement provides strong local exploitation. Aspiration rules and diversification mechanisms also allow the method to escape restrictive search patterns.

Despite these strengths, Tabu Search has several limitations. Its performance depends heavily on the design of the neighborhood, the tabu attributes, the tabu tenure, the candidate-list size, and the aspiration rule. An ineffective neighborhood may fail to produce meaningful improvements even when the memory system is well designed. Evaluating several neighboring candidates at every iteration may also be computationally expensive, especially when each candidate requires a complex simulation or model evaluation. Tabu Search also needs to be adapted to each problem because a useful move in routing may be very different from a useful move in scheduling or feature selection.

### 2.4 Particle Swarm Optimization

Particle Swarm Optimization was introduced by Kennedy and Eberhart (1995). It is a population-based metaheuristic inspired by collective behavior in bird flocks, fish schools, and other socially interacting groups. Each particle represents one possible solution and learns from both its own best result and the best result found by the swarm. A particle's next movement is influenced by its previous direction, its own best result, and the best result found by the swarm. The personal component encourages particles to use their own successful experience, while the social component encourages them to learn from the strongest solution discovered by the group. Momentum and personal attraction support exploration because particles retain their previous movement and may return to locations they individually found useful. Social attraction supports exploitation because the population moves toward the strongest known solution. If social influence becomes too strong, the swarm may converge prematurely around a local optimum. If personal influence becomes too strong, particles may move too independently and fail to benefit from collective information. Kennedy and Eberhart observed that a reasonable balance between personal and social influence produced the most effective search behavior.

Later PSO developments introduced an inertia weight that controls how strongly particles preserve their previous velocity. A high inertia weight encourages broader movement, while a lower value promotes refinement around known solutions. Many implementations gradually reduce inertia during the search so that the swarm begins with stronger exploration and ends with stronger exploitation. Other parameters control how strongly particles follow their own experience or the best solutions found by the swarm. Sengupta et al. (2019) emphasized that no PSO parameter configuration is universally optimal. Performance depends on the objective function, dimensionality, topology, population size, and diversity of the swarm. Parameter values should therefore be selected according to the problem and validated experimentally rather than treated as universal constants.

PSO performance is also affected by the swarm topology. PSO can control how widely information is shared between particles. Sharing information quickly can speed up convergence, but it can also cause the swarm to follow a poor solution too early. Slower information sharing may preserve more diversity and reduce the risk of premature convergence. Standard PSO was developed for continuous optimization. Route planning, scheduling, and feature selection are discrete or combinatorial, so the concepts of position and velocity must be adapted. Discrete PSO methods replace the original continuous movement with problem-specific ways of representing choices, such as binary feature selection or ordered job and route sequences.

Alharkan et al. (2020) used Geometric Particle Swarm Optimization for a scheduling problem involving two parallel machines and one shared setup server. Instead of using standard continuous movement, the algorithm generated new job orders using information from the current solution and other strong solutions. Huang et al. (2016) developed a modified discrete PSO for multi-objective flexible job-shop scheduling. Their representation contained an operation-sequence vector and a machine-assignment vector. The algorithm used specialized operators to keep schedules valid while balancing makespan and workload.

PSO has also been adapted to feature selection. Zhang et al. (2017) represented each feature through a continuous probability value and selected the feature when the value exceeded a threshold. Xie et al. (2021) used enhanced continuous PSO models whose positions were decoded into binary feature subsets. These studies show that discrete applications often preserve the social-learning principle of PSO while replacing its original movement equation with problem-specific operators.

Multi-objective PSO can keep several strong trade-off solutions instead of selecting only one overall best result. Zhang et al. (2017) used an external archive for multi-label feature selection, where the objectives were to minimize Hamming loss and minimize the number of selected features. Adaptive mutation and local differential learning were used to improve exploration and Pareto-front coverage. PSO is frequently hybridized with other optimization methods to address premature convergence and weak local refinement. Hybrid approaches combine PSO with other optimization or local-search methods, including Simulated Annealing and Tabu Search. Sengupta et al. identified hybridization as one of the most active areas of PSO research. However, they also noted that hybrid methods often contain many interacting mechanisms and parameters, making it difficult to determine which component produced the observed improvement.

Particle Swarm Optimization offers several advantages. It performs population-based exploration, shares information rapidly, can be implemented using relatively simple operations, and is compatible with parallel processing. Its population allows several areas of the search space to be examined simultaneously. However, it is vulnerable to premature convergence, stagnation, and loss of diversity. Its behavior depends on the quality of the leaders and the selected movement parameters. Discrete problems also require specialized representations and operators that may substantially change the behavior of the original algorithm.

### 2.5 Benchmark Optimization Problems

The present study focuses on three major categories of optimization problems: route optimization, job scheduling, and machine-learning feature selection. These problems were selected because they require different kinds of solutions. Routing focuses on the order of locations, scheduling involves assigning and ordering jobs, and feature selection involves choosing which features to keep. Using several problem categories may provide a broader understanding of the algorithms than testing them on one application alone. An algorithm that performs effectively in a continuous or permutation-based space may behave differently in a binary subset space. Differences in solution representation, neighborhood structure, objective cost, and constraint handling may favor different search strategies.

### 2.6 Route Optimization

Route optimization aims to find an efficient path between locations. A common example is the Traveling Salesman Problem, which asks for the shortest route that visits every city once and returns to the starting point. The quality of a route is usually measured by its total distance. The number of possible routes increases factorially with the number of cities. Consequently, exhaustive enumeration becomes impractical for large instances. This has made the Traveling Salesman Problem a common benchmark for evaluating exact algorithms, heuristics, and metaheuristics.

Grabusts et al. (2019) applied Simulated Annealing to an eight-location route involving dairy enterprises in Belarus. A 2-opt neighborhood generated new solutions by reversing a selected segment of the route. The reported route stabilized at approximately 648.69 kilometers. The study demonstrated a practical implementation of SA for route construction, but the small instance size limited the strength of its conclusions. The result was not compared with an exact optimum, only one principal stochastic outcome was reported, and the temperature and transition parameters were not documented in sufficient detail.

Zhan et al. (2016) provided stronger evidence through List-Based Simulated Annealing. Their method was tested on TSP instances ranging from dozens to tens of thousands of cities. The list-based temperature mechanism reduced dependence on manually selected cooling schedules, while a hybrid neighborhood combined inversion, insertion, and swapping. Their results showed that Simulated Annealing could remain competitive on very large routing instances when the cooling method and neighborhood design were carefully constructed.

Tabu Search has also been widely applied to route optimization because route changes can be represented naturally through edge exchanges, segment reversals, city insertion, and route swaps. A tabu list may store recently added or removed edges, preventing the algorithm from immediately reversing a route modification. Pirim et al. (2008) reviewed several routing studies and found that Tabu Search frequently produced stronger solution quality than Simulated Annealing and threshold-accepting methods, particularly as problem size increased. However, Tabu Search sometimes required more computation because it evaluated several route candidates at each iteration.

Ru (2024) applied Tabu Search to multimodal vehicle-logistics routing involving road, rail, and water transport. The model considered transfer costs, transportation time, facility capacity, and route profitability. The company case reported increased profit on most optimized routes. However, the paper contained inconsistencies in its runtime reporting and used classification measures such as recall and ROC-curve area in a routing context without sufficiently explaining their relevance.

Particle Swarm Optimization requires substantial adaptation for route problems because a route is a permutation rather than a continuous vector. Because routes are ordered sequences, PSO must be modified so that particles can represent and change valid routes. Sengupta et al. (2019) reviewed several PSO hybrids for route optimization, many of which combined PSO with local route-improvement methods or other optimization algorithms such as 2-opt or Simulated Annealing. These combinations allow PSO to examine several route regions simultaneously while relying on local operators to refine individual routes.

Overall, SA provides flexible route changes, TS uses memory to avoid repeating recent moves, and PSO can explore several routes at once but requires more modification. Hybrid local search often strengthens all three methods. A fair comparison should therefore measure route quality, objective evaluations, runtime, convergence speed, and consistency across repeated runs.

### 2.7 Job Scheduling and Machine Allocation

Job scheduling assigns operations to machines and determines their processing order. Common goals include finishing all jobs sooner, reducing delays, and balancing work between machines. Scheduling becomes increasingly difficult when it includes multiple machines, alternative machine assignments, setup times, shared servers, precedence constraints, due dates, or limited capacity. In the classical Job-Shop Scheduling Problem, each job contains several operations that must be processed on specified machines in a predetermined order. The objective is commonly to minimize makespan, which is the completion time of the final operation.

Watson et al. (2005) showed that the search space contains many local and near-local-optimal schedules. They found that more structured scheduling problems could be harder because Tabu Search had to explore a wider range of possible schedules. In Flexible Job-Shop Scheduling, some jobs can be handled by more than one machine. The scheduler must therefore decide both which machine should handle each job and in what order. Huang et al. (2016) treated this as a multi-objective problem and minimized makespan, total machine workload, and maximum individual machine workload. Their modified discrete PSO produced several strong scheduling trade-offs on standard benchmark problems.

Alharkan et al. (2020) studied a scheduling problem involving two identical parallel machines served by one setup server. Each job required a setup period and a processing period. Since only one server could perform setup at a time, the algorithm had to coordinate server availability with machine availability. The study compared Tabu Search, Geometric Particle Swarm Optimization, Simulated Annealing, a Genetic Algorithm, and Iterated Local Search. Tabu Search produced the lowest worst-case average error ratio and most frequently reached the theoretical lower bound for large instances. GPSO generally ranked second, while Simulated Annealing and the Genetic Algorithm performed strongly on small instances but deteriorated as problem size increased.

Jwo et al. (2023) applied Tabu Search to manufacturing-order sequencing in an aircraft-industry work center. Their model considered daily capacity, due dates, processing times, remaining lead time, and unfinished orders carried into subsequent days. The neighborhood swapped delayed manufacturing orders with other orders. When initialized using First In, First Out, the method reached the theoretical lower bound for the number of delayed orders on all five tested days. Its total expected delay also remained close to the ideal reference values.

Simulated Annealing represents a schedule as one current sequence or assignment. Neighboring schedules may be generated by swapping jobs, inserting an operation, reversing part of a sequence, or changing a machine assignment. Its probabilistic acceptance rule allows the search to leave locally optimal schedules. However, difficult scheduling instances may require many evaluations before the cooling schedule produces sufficiently focused refinement. Alharkan et al. found that Simulated Annealing reached the lower bound in all eight-job cases but did not maintain the same performance as the number of jobs increased.

Tabu Search is especially common in scheduling because job exchanges, operation movements, and machine reassignments naturally define neighborhoods. Its memory can track recent job swaps or machine assignments so that the search does not immediately repeat the same decisions. Tabu Search generally performs well when its job-swap rules are useful and its tabu settings prevent repetition without blocking too many good moves.

Particle Swarm Optimization must be modified for scheduling because continuous particle movement does not naturally preserve valid job permutations or operation precedence. Discrete PSO scheduling methods replace velocity movement with crossover, swaps, probability vectors, and decoding procedures. Their population-based nature allows several schedule regions to be examined simultaneously, but maintaining validity requires more complex operators than standard PSO.

The scheduling literature generally indicates that Tabu Search performs strongly on medium and large combinatorial instances. Discrete PSO variants can also scale effectively when their representation preserves feasible schedules and maintains diversity. Simulated Annealing may perform well on small or moderately sized instances but can require longer computation on difficult problems. These conclusions remain dependent on the scheduling formulation, neighborhood operators, evaluation limits, and parameter settings used by each study.

### 2.8 Machine-Learning Feature Selection

Feature selection is the process of identifying a subset of relevant variables from a larger feature set. For a dataset containing *n* features, there are 2^n possible subsets. Even a moderate number of variables therefore creates a very large combinatorial search space. Feature selection aims to remove unnecessary or redundant features while keeping good predictive performance. This can also reduce training time and make the model easier to understand. Removing unnecessary features may also reduce overfitting, particularly when the number of available training samples is small relative to the number of variables.

Feature-selection methods can use simple statistical measures or repeatedly test different feature subsets using a machine-learning model. The second approach can capture interactions between features but usually requires more computation. Allvi et al. (2020) applied Simulated Annealing to feature selection for learning-to-rank systems. A state represented a feature subset of fixed size, while a neighboring state was created by replacing selected feature indices. The study used LambdaMART and measured the quality of each feature subset using a ranking-performance score. The search was repeated for each possible subset size. The authors reported that subsets containing approximately 18 to 39 features could match or exceed the performance of the complete feature sets across six benchmark datasets. Their findings suggested that some original features were redundant or harmful. However, the study used random feature selection as its main baseline, did not report sufficiently detailed repeated-run statistics, omitted several important Simulated Annealing parameters, and appeared to use test performance during feature selection. This may have made the reported results appear better than they would be on completely unseen data.

Zhang and Sun (2002) applied Tabu Search to both fixed-size and minimum-size feature selection. The method tested feature subsets by adding, removing, or replacing selected features. The method was compared with several common feature-selection methods, including Genetic Algorithms and Branch and Bound. In synthetic experiments involving 30, 60, and 100 features, Tabu Search generally produced better best, mean, and worst objective values than the Genetic Algorithm under similar or lower evaluation costs. In a 20-feature fixed-size task, Tabu Search reached the Branch-and-Bound optimum in all 20 runs when selecting 10 features. The study also found that Tabu Search performance depended on its tabu settings and the size and design of the candidate neighborhood.

Xie et al. (2021) developed two enhanced PSO methods, PSOVA1 and PSOVA2, for wrapper-based feature selection. Their evaluation used a K-Nearest Neighbor classifier and combined classification accuracy with feature reduction. Accuracy received substantially greater weight than subset size. PSOVA1 and PSOVA2 added several mechanisms intended to improve exploration, strengthen promising particles, and reduce premature convergence. Across 13 datasets containing from 30 to 22,283 features, the proposed methods achieved the highest reported accuracy and F-score among the compared algorithms. PSOVA2 significantly outperformed the baseline methods on eight datasets. However, the proposed algorithms were highly complex. Their improvements resulted from PSO combined with several additional mechanisms, making it difficult to determine how much of the benefit came from the basic swarm structure itself.

Zhang et al. (2017) treated multi-label feature selection as a two-objective problem. The algorithm simultaneously minimized Hamming loss and the number of selected features. It kept several strong trade-off solutions and used additional mechanisms to preserve diversity during the search. Across six datasets, the method generally produced better trade-off solutions than the comparison methods. The study demonstrated that feature selection does not always need to be converted into one weighted objective. Multi-objective optimization can preserve several useful trade-offs between predictive performance and dimensionality.

The feature-selection literature indicates that all three algorithms can search large subset spaces. Simulated Annealing provides a simple mechanism for moving among subsets but requires careful cooling and repeated model evaluations. Tabu Search provides explicit memory and strong neighborhood control. Particle Swarm Optimization can examine several feature subsets at once, but it may lose diversity and requires a suitable binary or probability-based representation. A fair comparison of feature-selection algorithms should evaluate predictive performance, subset size, runtime, objective evaluations, convergence, and stability across repeated trials. The same classifier, preprocessing method, training-validation-test partition, and performance metric should be used for all algorithms. Candidate subsets should be selected using training or validation data, while test data should be reserved for final evaluation.

### 2.9 Comparative Studies of Simulated Annealing, Tabu Search, and Particle Swarm Optimization

Several reviewed studies directly compared two or more of the selected metaheuristics. These comparisons provide evidence regarding solution quality, convergence, computational efficiency, and search behavior, although their findings remain dependent on the problem and experimental conditions.

Zhang and Nicholson (2018) compared Boltzmann Simulated Annealing, Very Fast Annealing, Tabu Search, and Particle Swarm Optimization for tuning a parameter in the Parameterized Dynamic Slope Scaling Procedure for Fixed-Charge Network Flow. The study included 180 generated network instances. All four methods improved most of the tested instances, and none was statistically superior in final solution quality. The main difference was computational efficiency. Particle Swarm Optimization produced the greatest improvement per iteration and was fastest on small and large instances. Tabu Search remained competitive on the largest instances, while both Simulated Annealing variants required substantially more computation. The study demonstrates that similar final objective values may conceal meaningful differences in convergence and evaluation efficiency.

Youssef et al. (2001) compared a Genetic Algorithm, Simulated Annealing, and Tabu Search on VLSI floorplanning under a shared budget of 5,000 objective evaluations. The objective combined circuit area, wire length, and delay through a fuzzy membership score. Across five circuits, the reported ranking was Tabu Search first, Genetic Algorithm second, and Simulated Annealing third. Tabu Search reached strong solutions quickly, while the Genetic Algorithm later plateaued and Simulated Annealing required more evaluations in weaker regions. However, the cost-inflation experiment showed that its poor performance was partly caused by a mismatch between the fuzzy objective scale and the temperature schedule. This emphasizes that algorithm comparisons must consider whether each method has been calibrated appropriately.

Alharkan et al. (2020) compared Tabu Search, Geometric Particle Swarm Optimization, Simulated Annealing, a Genetic Algorithm, and Iterated Local Search on the two-machine single-server scheduling problem. Tabu Search produced the lowest worst-case average error and most frequently reached the theoretical lower bound on large instances. Geometric Particle Swarm Optimization ranked second overall. Simulated Annealing and the Genetic Algorithm were competitive for smaller instances but deteriorated as the number of jobs increased.

Pirim et al. (2008) reviewed many studies comparing Tabu Search with Simulated Annealing, Genetic Algorithms, Particle Swarm Optimization, and Ant Colony Optimization. Their findings indicated that Tabu Search frequently performed strongly in scheduling, routing, facility location, and production planning. However, they also identified cases in which Simulated Annealing produced better schedules or Genetic Algorithms performed better because their representation reduced the number of candidate solutions. Algorithm rankings also changed according to whether comparisons were controlled by runtime, evaluated solutions, or unrestricted convergence. The review therefore supports a problem-dependent rather than universal interpretation of performance.

Mhamdi et al. (2011) compared standard PSO with several hybrid forms in microwave imaging. In one experiment, the full PSO-SA-TS hybrid produced the lowest reconstruction error compared with standard PSO and the partial hybrids. The complete hybrid also reduced computation time in another experiment. The authors attributed the improvement to the combination of Particle Swarm Optimization's population-level exploration, Simulated Annealing's probabilistic local escape, and Tabu Search's memory-based refinement. However, the study did not compare full standalone implementations of SA and TS under the same reconstruction problem, so its findings primarily support the value of hybridization rather than a direct ranking of the three independent methods.

The comparative literature shows that no one algorithm consistently dominates all problem categories. Tabu Search frequently performs strongly on neighborhood-intensive combinatorial problems. Particle Swarm Optimization often demonstrates strong efficiency and scalability when an appropriate representation is available. Simulated Annealing can produce competitive final quality but may require more evaluations and careful calibration of temperature and objective scale. Hybrid methods may combine complementary strengths, although they also increase implementation complexity and parameter interactions.

### 2.10 Evaluation Criteria Used in Previous Studies

The reviewed studies used different evaluation measures depending on the optimization problem. Studies commonly measured solution quality using best and average results, error from a known solution, or how often an algorithm reached the optimum. Reporting only the best result is insufficient because it does not show how consistently a stochastic algorithm performs.

Computational efficiency was measured through CPU time, number of iterations, number of objective-function evaluations, improvement per iteration, and convergence speed. Raw iteration counts should be interpreted cautiously because the meaning of one iteration differs among the algorithms. One Tabu Search iteration may evaluate several candidates, one Simulated Annealing transition may evaluate only one neighbor, and one PSO iteration evaluates the complete swarm. Equal numbers of objective evaluations or equal runtime budgets may therefore provide a fairer comparison than equal iteration counts.

Stability should be evaluated through repeated independent runs. Repeated runs can be summarized using average results, variation, and success frequency. Repeated trials are particularly important for Simulated Annealing and Particle Swarm Optimization because their search paths depend heavily on random choices. Tabu Search may also require repeated trials when it uses random initialization, neighborhood sampling, or tie-breaking.

Multi-objective studies use measures that consider both how good the trade-off solutions are and how well they are distributed. These metrics assess not only convergence toward the Pareto front but also the diversity and distribution of trade-off solutions. Feature-selection studies use classification accuracy, F-score, precision, recall, Hamming loss, and Normalized Discounted Cumulative Gain. The selected metric should match the predictive task and should be evaluated on data not used to guide the optimization process. The number or percentage of selected features should also be reported so that improvements in predictive performance are not achieved solely by retaining nearly every variable. Several studies also used statistical tests to determine whether performance differences were likely to be meaningful rather than caused by random variation. The statistical method used should still match the type of results being analyzed.

### 2.11 Issues and Limitations in Existing Literature

Parameter sensitivity is a recurring issue across all three algorithms. All three algorithms depend on several parameter choices. SA is sensitive to its temperature and cooling settings, TS depends on its memory and neighborhood settings, and PSO depends on its swarm and movement parameters. Parameter values that perform well for one problem may perform poorly for another. Many studies select parameters heuristically or copy values from earlier literature without systematic tuning. This makes it difficult to determine whether poor performance results from the algorithm or from unsuitable parameter selection. Too much tuning on the same test problems may also make results look better than they would on new problems.

Experimental conditions are often inconsistent across studies. Algorithms may be implemented using different datasets, hardware, programming languages, computational budgets, stopping rules, and levels of optimization. Some studies compare a newly implemented algorithm with numerical results copied from earlier papers instead of rerunning all methods in the same environment. These differences make it difficult to know whether the results are caused by the algorithms themselves or by the way the experiments were set up.

Repeated-run reporting is also frequently inadequate. Some studies report only one run, one best result, or a mean without standard deviation. This is insufficient for stochastic optimization because one unusually favorable run may create a misleading impression of performance. Reliable evaluation requires several independent trials and measures of variation.

Several reviewed studies were conducted on small or synthetic problems. Grabusts et al. (2019) used only eight route locations, which is small enough for exact enumeration. Zhang and Sun (2002) used synthetic variable-size feature-selection problems containing 30 to 100 features, which are modest relative to modern datasets containing thousands of variables. Other studies used randomly generated scheduling instances or synthetic error models. Such experiments provide controlled conditions but may not represent the uncertainty, dynamic conditions, and operational constraints of real applications.

Weak or inappropriate baselines are another concern. Some studies compared a proposed method only with its immediate predecessor, random selection, or previously published results. Niño et al. (2012) constructed the reference Pareto front from the outputs of the same two algorithms being compared, weakening the interpretation of its perfect recovery results. Allvi et al. (2020) primarily compared Simulated Annealing with random feature selection rather than stronger established feature-selection methods; its unclear use of test data during optimization further limits the independence of the reported evaluation.

Some papers omitted critical implementation details such as random seeds, exact initial and final temperatures, complete cooling schedules, neighborhood-sampling procedures, archive limits, and precise stopping conditions. Missing details reduce reproducibility and make it difficult to determine whether performance differences reflect algorithmic behavior or implementation choices.

Hybrid methods present an additional interpretive challenge. Hybrid algorithms often combine several additional search mechanisms, making it difficult to know which part actually caused the improvement. Increased complexity also creates more parameters and a greater risk of overfitting the algorithm to the selected benchmark set.

### 2.12 Synthesis of the Reviewed Literature

The reviewed studies establish that Simulated Annealing, Tabu Search, and Particle Swarm Optimization are all capable of solving difficult optimization problems, but they rely on substantially different search mechanisms. Simulated Annealing maintains one current solution and uses temperature-dependent acceptance to control its movement. Its major strength is its ability to cross inferior regions and escape local optima. Its main weakness is its sensitivity to cooling settings and the way the objective function is scaled. A carefully designed neighborhood and temperature schedule can make the method competitive on large problems, while poor calibration can cause excessive computation in low-quality regions.

Tabu Search also works with one current solution, but it uses memory to guide which nearby solution should be tried next. It often performs well in scheduling, routing, and feature-selection problems because its memory can guide the search around nearby solutions. Its effectiveness depends on meaningful neighborhood operators, appropriate tabu tenure, and sufficiently informative candidate evaluation. Excessive restrictions or poorly selected tabu attributes may weaken performance.

Particle Swarm Optimization maintains a population of candidate solutions and uses personal and social learning. Its population can examine several regions at the same time, and its simple information-sharing mechanism can produce rapid convergence. However, the swarm may lose diversity and converge prematurely around a local optimum. Discrete problems also require specialized representations that may substantially alter the original continuous PSO mechanism.

Across direct comparisons, no algorithm consistently dominates every problem. Tabu Search often performs well on problems where useful nearby solutions can be created through simple changes. Particle Swarm Optimization often provides efficient convergence and scalability when its discrete representation is appropriate. Simulated Annealing can produce competitive solutions but may require more evaluations and greater care in parameter calibration. Hybrid algorithms can combine the strengths of several methods, but their added complexity makes it harder to know which part actually caused the improvement.

The relative performance of the algorithms depends on problem type, problem size, encoding, neighborhood or movement design, parameter values, evaluation budget, stopping conditions, and implementation quality. One algorithm should therefore not be declared universally superior based on isolated experiments. A controlled comparison should examine both final solution quality and the process by which that quality is obtained.

### 2.13 Numeric Benchmarks from the RRL Corpus

To anchor Section 5 against reported numbers (not only narrative themes), **Table 1** summarizes key quantitative outcomes from the group's reviewed sources. Cross-paper numeric equality is not expected because problem classes, budgets, and hybrid variants differ; the table supports **directional** comparison.

**Table 1.** Reported results from key RRL sources (standalone SA/TS/PSO where available).

| Source | Domain | Setting | Reported numbers | Stated reasons |
|--------|--------|---------|------------------|----------------|
| Zhan et al. (2016) | TSP | TSPLIB; 25 trials | LBSA PEav 0.15–0.49%; eil51 0% gap | List cooling; hybrid neighborhood |
| Glover (1989) | TSP | Hard instances | Beats 3-opt bests; 75-city tour 553 | Tabu memory; aspiration |
| Pirim et al. (2008) | Routing | VRP survey | TS > SA; gap grows with size | Memory; neighborhood; init helps TS |
| Ru (2024) | Logistics | TS vs GA vs SA | Cost 1.2 vs 3.2–3.8; ~95% accuracy | Tabu avoids local traps |
| Alharkan et al. (2020) | Scheduling | n≤1000 | TS 1.032×LB; GPSO 1.036; SA 1.050 | TS cuts idle time; SA loses LB hits |
| Jwo et al. (2023) | Scheduling | Factory swap | TS+FIFO hits bound; FIFO +37% | Initial schedule dominates |
| Youssef et al. (2001) | VLSI | 5000 evals | TS > GA > SA | Cost scaling affects SA |
| Zhang & Sun (2002) | FS | 30-d wrapper | Tabu 12.22 vs GA 12.41 | Intensification; fewer evals |
| Mhamdi et al. (2011) | Hybrid | PSO vs hybrid | Error 0.105 vs 0.003 | Pure PSO premature convergence |
| Zhang & Nicholson (2018) | Network flow | 180 instances | SA/TS/PSO ~10.2–10.3% gap gain | Methods tie when structure similar |

### 2.14 Research Gap

Previous studies have applied Simulated Annealing, Tabu Search, and Particle Swarm Optimization to route optimization, scheduling, and feature selection. However, most studies focus on one application domain and use highly problem-specific implementations. Existing findings remain difficult to compare because studies use different problems, datasets, algorithm versions, parameters, and evaluation methods. Some comparisons measure runtime, while others use iteration count or objective evaluations. Several studies do not report repeated-run statistics or formal significance tests. Others compare heavily modified or hybrid algorithms with basic implementations, making it difficult to determine whether observed improvements result from the fundamental algorithm or from additional operators.

The three selected problem categories also have substantially different structures. Route optimization commonly uses permutations of locations. Scheduling combines sequencing, resource assignment, precedence, and capacity constraints. Feature selection uses binary subsets and may require an expensive predictive-model evaluation for every candidate. These differences may favor different search mechanisms. Tabu Search may benefit from clearly defined discrete neighborhoods, Particle Swarm Optimization may benefit from population diversity when encoding matches the domain, and Simulated Annealing may benefit from flexible stochastic movement.

This study addresses the gap by applying the **same three standalone algorithms** across routing, scheduling, and wrapper feature selection under one unified protocol with equal evaluation budgets, disjoint tuning and comparison sets, literature-informed tuning grids, and 30 independent seeds per algorithm per benchmark. Sample-test rankings and mechanisms are compared against Table 1 rather than expecting point equality of gap percentages across unrelated studies.

### 2.15 Significance of the Present Study

The study has theoretical, methodological, and practical significance. First, it compares three algorithms that search for solutions in different ways. Looking at them across routing, scheduling, and feature selection may help explain why certain algorithms are better suited to some problems than others. The study also highlights how differences in datasets, parameters, stopping rules, and evaluation methods can affect comparisons between algorithms. This approach addresses several weaknesses identified in previous research, including inconsistent budgets, incomplete parameter descriptions, missing variation measures, and comparisons conducted under different experimental environments.

From a practical perspective, the findings may support algorithm selection across several domains. Route-planning practitioners may prioritize distance reduction, runtime, and route stability. Production and manufacturing planners may prioritize makespan, machine utilization, tardiness, and schedule feasibility. Machine-learning practitioners may prioritize predictive performance, dimensionality reduction, and training cost. By comparing the algorithms across different problems, the study may help researchers and practitioners choose a method based on what the problem actually requires instead of assuming that one algorithm is always best.

---

## 3. METHODOLOGY

### 3.1 Overall Design

1. **Literature comparison** — qualitative review (§2) plus numeric synthesis (§2.13).  
2. **Sample tests** — identical algorithm implementations, shared fairness rules in `config/decisions.yaml`.

Fairness rules: equal **objective-evaluation** budget per run; disjoint tuning vs comparison instances; literature-informed tuning grids; **30 independent seeds** per algorithm per comparison instance; frozen winner parameters after tuning.

### 3.2 Experimental Platform and AI Assistance

Sample tests ran in a custom Python platform (FastAPI, React dashboard, CSV/JSON under `results/`). Development was AI-assisted for prototyping runners and UI. Researchers retained control of research questions, benchmark selection, fairness protocol, tuning grids, frozen parameters, execution, and all interpretations. Reported numbers come from executed runs only.

### 3.3 Algorithms and Per-Iteration Cost

- **SA:** one neighbor evaluated per step.  
- **TS:** candidate_list_size neighbors per step (100 TSP, 40 JSP, 30 FS).  
- **PSO:** random-key decode (TSP/JSP); threshold decode (FS); swarm_size evaluations per step.

Under equal evaluation budgets, TS and PSO perform fewer outer iterations than SA but more evaluations per iteration (§4.2).

### 3.4 Parameter Tuning and Comparison Matrix

| Domain | Tuning instances | Comparison instances | Budget | Metric |
|--------|------------------|----------------------|--------|--------|
| TSP | eil51, berlin52, st70 | kroA100, ch130, rat195 *(§5.1 also reports tuning instances for transparency)* | 100,000 | Mean gap % |
| JSP | ft10, ta01, ta21 | abz5, ta02, ta22, ta31, ta51 | 50,000 | Mean gap % |
| FS | ZooEW, IonosphereEW, SonarEW | BreastEW, WineEW, LymphographyEW, SpectEW | 5,000 | Mean best objective |

Frozen parameters: `results/tuning/selected_parameters.json`, `jsp_selected_parameters.json`, `fs_selected_parameters.json`.

### 3.5 Domain Setup and Known Limitations

**TSP:** SA and TS start from nearest-neighbor tours (~13–32% above optimum on eil51 in our runs). Gap % = (distance − optimum) / optimum × 100. **PSO exception:** although configs set `initial_solution: nearest_neighbor`, the PSO implementation initializes particles from uniform random keys in [0,1]^d and never decodes the configured NN tour into the swarm; eil51 PSO runs therefore start near **214–250%** above optimum versus **~13–32%** for SA/TS. Reported PSO TSP gaps measure this protocol asymmetry (and random-key search from extreme starts), not fairly initialized standalone PSO. Elitist best-solution tracking is in decoded tour space, but the missing shared initializer invalidates cross-algorithm TSP comparison for PSO.

**JSP:** Shared job-major initializer (`longest_processing_time`) produces a weak identical start for all algorithms (~400–990% above BKS before search vs ~50–70% for random shuffle). **Relative** rankings remain fair; **absolute** gaps are pessimistic (cf. Jwo et al. on initialization).

**FS:** Wrapper objective = α·CV loss + β·feature ratio (α=0.9, β=0.1 in all runs); kNN on **raw** EW features without per-fold standardization; test scores recorded but not used in search. This differs from common wrapper practice (scaled features; lighter sparsity penalties such as α=0.99/β=0.01 in Xie et al., 2021).

### 3.6 Pilot Tests and Protocol Evolution

Before the full matrix, exploratory pilots (10 runs, one instance per domain, 20k evaluations) identified an SA cooling-schedule scaling bug on TSP and informed budget-fair iteration design. Pilots showed SA ahead on one 50-city TSP and TS ahead on Breast Cancer FS; the full 30-seed multi-instance study supersedes pilots for final rankings (§5.0, Appendix B).

---

## 4. FORMAL AND THEORETICAL ANALYSIS

### 4.1 Computational Characterization

**SA** maintains state s_k, generates neighbor s′ via move operator N(s_k). Accept if f(s′) ≤ f(s_k); else accept with probability exp(−(f(s′)−f(s_k)) / T_k). Temperature updates by geometric cooling T_{k+1} = α·T_k.

**TS** selects s_{k+1} = argmin_{s′ ∈ N(s_k) \ Tabu} f(s′), unless aspiration (f(s′) < f_best) overrides tabu status.

**PSO** updates v_i(t+1) = w·v_i(t) + c1·r1·(pbest_i − x_i) + c2·r2·(gbest − x_i); then x_i(t+1) = x_i(t) + v_i(t+1).

### 4.2 Per-Iteration Computational Complexity

**Table 2.** Dominant per-iteration cost (d = dimensionality, m = TS list size, n = swarm size).

| Algorithm | Evals/iter. | Update cost | Memory |
|-----------|-------------|-------------|--------|
| SA | O(1) | O(d) | O(1) |
| TS | O(m) | O(m·d) | O(t) |
| PSO | O(n) | O(n·d) | O(n·d) |

Under evaluation-budget fairness, TS with m=100 performs roughly 100× fewer outer iterations than SA for the same evaluation count—explaining early TS plateaus when neighborhoods are exhausted relative to remaining budget.

### 4.3 Convergence Properties

Finite geometric SA schedules used in practice have **no** global optimality guarantee. Asymptotic convergence in probability under logarithmic cooling is established in the annealing literature (Hajek, 1988; Geman & Geman, 1984), not in Kirkpatrick et al. (1983), which introduced the method empirically. TS has no probabilistic convergence guarantee—behavior is bounded by neighborhood coverage unless diversified. PSO has no global guarantee; premature diversity loss is a convergence-theoretic weakness (Sengupta et al., 2019).

### 4.4 Representation and State-Space Considerations

TSP uses permutation space; JSP joint sequencing space; FS binary hypercube {0,1}^d. SA and TS operate via problem-defined moves. Standard PSO optimizes in ℝ^d and maps to combinatorial spaces through decoders (random keys, sigmoid thresholding). This encoding step is a formal source of distortion—predicting largest PSO penalty on TSP/JSP and smallest on native binary FS (§5.4).

---

## 5. RESULTS, DISCUSSION, AND COMPARATIVE EVALUATION FRAMEWORK

All completed full tests use **30 seeds** per algorithm per instance.

**Literature-alignment verdicts** (Tables 5, 7, 8b, 9): **Confirmed** = same ranking direction as cited literature; **Supported** = directionally consistent with caveats (scale, hybrid variant, or protocol difference); **Partial** = mixed or calibration-sensitive; **Unresolved** = outcome reflects a documented protocol or implementation issue rather than algorithm capability.

### 5.0 Pilot vs Full Study Reconciliation

**Table 3.** Exploratory pilots (10 runs, 20k evals, single instance) vs full protocol.

| Domain | Pilot setting | Pilot winner | Full-protocol winner | Reconciliation |
|--------|---------------|--------------|----------------------|----------------|
| TSP | 50 cities | SA (581.7 vs TS 694.4) | **TS all 6 instances** | Pilot TS plateaued early (list=20); full study uses list=100, 100k evals, multi-instance tuning |
| JSP | FT06 (opt=55) | SA = TS (both optimal) | **TS all 5** | Small instance hides scale effect; large Taillard shows TS > PSO > SA |
| FS | Breast Cancer | TS (0.0276) | **TS/PSO tie best** on 3/4; all tie WineEW | Consistent; PSO closes gap vs permutations |

Pilot TSP reversal after SA schedule correction demonstrates Youssef-style calibration sensitivity; it does **not** overturn Pirim-style TS routing advantage at full scale.

### 5.1 Traveling Salesman Problem (18/18 complete)

**Table 4.** Gaps vs known optima (best-of-30 / mean-of-30).

| Instance | Cities | Optimum | SA | TS | PSO |
|----------|--------|---------|----|----|-----|
| eil51 | 51 | 426 | 13.15% / 24.19% | **2.35% / 4.40%** | 65.73% / 97.72% |
| berlin52 | 52 | 7,542 | 8.46% / 23.60% | **0.33% / 3.40%** | 57.94% / 102.72% |
| st70 | 70 | 675 | 18.96% / 23.97% | **3.85% / 6.29%** | 113.48% / 179.81% |
| kroA100 | 100 | 21,282 | 19.47% / 26.83% | **10.38% / 13.64%** | 211.84% / 293.61% |
| ch130 | 130 | 6,110 | 18.31% / 25.02% | **17.55% / 20.25%** | 264.45% / 324.59% |
| rat195 | 195 | 2,323 | 13.52% / 19.62% | **13.52% / 19.34%** | 222.47% / 249.51% |

Mean runtime per 100k evals: TS ~3–9 s; SA ~20–40 s; PSO ~3–7 s.

**Table 5.** TSP — literature vs this study.

| Topic | Literature | Our tests | Verdict |
|-------|------------|-----------|---------|
| Routing winner | TS often best (Pirim; Glover) | TS all 6 | Confirmed |
| Gap scale | LBSA <0.5% PEav (Zhan) | TS 0.33–4% (≤70 cities); 10–18% (≥100) | Ranking yes; gaps wider |
| SA role | Competitive if calibrated | Second; high seed variance | Partial |
| Scalability | TS–SA gap may shrink (Pirim) | Tie best gap at rat195 (13.52%) | Supported |
| PSO permutations | Hybrids needed (Mhamdi; Sengupta) | 58–264% gap under **broken NN init** | **Unresolved** (protocol) |

**TSP generalization note:** On tuning instances (eil51, berlin52, st70), TS mean best gap ≈ **2.2%** vs SA ≈ **13.5%**; on held-out instances (kroA100, ch130, rat195), TS ≈ **13.8%** vs SA ≈ **17.1%**—a **6.3×** TS degradation tuning→held-out versus **1.3×** for SA. TS still wins every instance, but the abstract routing lead is partly tuned-set strength; held-out gaps are the fairer generalization read.

**RQ1:** TS delivers best route quality; SA is viable second choice. PSO TSP numbers are withheld from ranking claims pending NN-consistent initialization.

### 5.2 Job-Shop Scheduling (15/15 complete)

**Table 6.** Gaps vs best known makespan.

| Instance | Size | BKS | SA | TS | PSO |
|----------|------|-----|----|----|-----|
| abz5 | 10×10 | 1,234 | 14.51% / 21.60% | **1.78% / 5.10%** | 3.16% / 8.28% |
| ta02 | 15×15 | 1,244 | 37.54% / 44.14% | **8.28% / 14.00%** | 11.41% / 18.63% |
| ta22 | 20×20 | 1,600 | 56.69% / 62.57% | **19.50% / 27.57%** | 22.94% / 31.67% |
| ta31 | 30×15 | 1,764 | 57.88% / 63.20% | **17.46% / 25.33%** | 23.47% / 31.78% |
| ta51 | 50×15 | 2,760 | 54.31% / 58.95% | **21.12% / 27.46%** | 30.91% / 36.87% |

**Table 7.** JSP — literature vs this study.

| Topic | Literature | Our tests | Verdict |
|-------|------------|-----------|---------|
| Scheduling winner | TS strong at scale (Alharkan) | TS best all 5 | Confirmed |
| PSO vs SA | GPSO 2nd (Alharkan) | PSO < SA gap on **all 5** held-out instances (incl. abz5) | Supported |
| SA large instances | SA loses LB hits (Alharkan) | SA 54–58% on ta22+ | Directional |
| Absolute gaps | ~3% above LB (Alharkan) | 17–57% above BKS | Not comparable (init, problem class) |

**RQ2:** TS leads makespan quality on all five held-out JSP instances; PSO consistently ranks second (better gap than SA on every instance, including abz5). JSP is the strongest evidence block: disjoint tuning/comparison sets, shared initializer, and consistent TS > PSO > SA ordering.

### 5.3 Feature Selection (12/12 complete)

**Table 8.** Wrapper objective (lower is better; 30 runs).

| Dataset | Features | SA best / mean (std) | TS best / mean (std) | PSO best / mean (std) |
|---------|----------|----------------------|----------------------|------------------------|
| BreastEW | 30 | 0.2926 / 0.3008 (0.0029) | **0.2793 / 0.2793 (0.0000)** | **0.2793 / 0.2844 (0.0038)** |
| WineEW | 13 | 0.5986 / 0.6037 (0.0036) | **0.5986 / 0.5986 (0.0000)** | **0.5986 / 0.5991 (0.0019)** |
| LymphographyEW | 18 | 0.1981 / 0.2236 (0.0113) | **0.1911 / 0.2291 (0.0301)** | **0.1911 / 0.2210 (0.0147)** |
| SpectEW | 22 | 0.1580 / 0.1704 (0.0058) | **0.1535 / 0.1686 (0.0104)** | **0.1535 / 0.1639 (0.0063)** |

Mean runtime per 5k evals: SA ~72–103 s; TS ~73–83 s; PSO ~235–318 s (swarm evaluates 30 particles per step). BreastEW best seeds: TS and PSO both reached 0.2793 (TS: 1 feature, CV 0.693; PSO best run: comparable subset); SA best 0.2926 (9 features).

**Table 8b.** FS — literature vs this study (RQ3, RQ5).

| Topic | Literature | Our tests | Verdict |
|-------|------------|-----------|---------|
| TS vs GA in wrappers | Tabu wins with fewer evals (Zhang & Sun) | TS lowest mean on **2/4** (BreastEW, WineEW); PSO lowest on LymphographyEW & SpectEW | Partial |
| SA in wrappers | SA > random (Allvi) | SA within ~0.02 of TS/PSO best | Supported |
| Algorithm spread | ~2% criterion spread (Tabu vs GA) | ~0.01–0.05 objective spread all three | Supported |
| PSO on FS | Enhanced PSO wins benchmarks (Xie) | **Baseline PSO matches TS best on 3/4** | Supported for encoding; not enhanced variant |
| PSO vs permutations | PSO collapses without adaptation (Sengupta) | PSO **competitive on FS**, worst on TSP | Confirmed (§4.4) |

**RQ3:** Wrapper FS shows a narrow objective band, but interpret cautiously: kNN uses **raw EW features without in-fold standardization** (WineEW proline-scale dominance); weights are **α=0.9, β=0.1** (heavier reduction pressure than the α=0.99/β=0.01 convention in Xie et al., 2021). WineEW best solutions select **one feature** at CV score **0.34** (below the **0.40** majority baseline)—suggesting a degenerate objective landscape, not necessarily encoding advantage. TS has zero std on BreastEW/WineEW means but **higher** variance than PSO on LymphographyEW and SpectEW. PSO matches TS at best-seed on three datasets; overall mean objective is slightly best for PSO (0.317 vs TS 0.319 vs SA 0.325).

### 5.4 Cross-Domain Patterns

| Pattern | TSP | JSP | FS |
|---------|-----|-----|-----|
| Best quality (best-of-30) | TS | TS | TS = PSO (3/4); all tie WineEW |
| Best mean stability | TS | TS | Mixed (TS on Breast/Wine; PSO on Lymph/Spect) |
| Second | SA | PSO (large) | SA or PSO (dataset-dependent) |
| Weakest | PSO | SA (large) | SA (best-seed, 3/4) |
| PSO encoding penalty | Severe | Moderate | **Low** — matches native binary form |

### 5.5 Integrated Literature Alignment (RQ5)

**Table 9.** RRL expectations vs sample tests.

| Expectation | Literature | Our result | Verdict |
|-------------|------------|------------|---------|
| TS wins routing/scheduling | Pirim; Glover; Alharkan | TS 11/11 instance wins | Confirmed |
| PSO weak on permutations | Sengupta; Mhamdi | PSO worst TSP *(protocol)*; 2nd on JSP | Partial |
| SA calibration-sensitive | Youssef | SA 2nd TSP; weak large JSP | Partial |
| FS narrow spread | Zhang & Sun (~2%) | <0.05 obj spread SA/TS/PSO | Confirmed |
| PSO competitive on binary FS | Xie et al. (enhanced variants) | PSO matches TS best 3/4 | Confirmed (baseline) |
| Hybrids beat standalone PSO | Mhamdi 0.003 vs 0.105 | Standalone only | Out of scope |
| No free lunch | Pirim; NFL | Domain-dependent ranking | Confirmed |

Rankings align; gap magnitudes differ because literature often reports tuned/hybrid variants, JSP shared weak initializer inflates absolute gaps, and evaluation-budget fairness changes convergence shape.

### 5.6 Comparative Evaluation Framework

**Table 10.** Practical guidance.

| Criterion | SA | TS | PSO |
|-----------|----|----|-----|
| Quality (permutation) | Moderate; seed-sensitive | **Best** in our tests | Poor standalone |
| Quality (wrapper FS) | Competitive | Best mean on 2/4 datasets | Best mean on 2/4; matches TS best on 3/4 |
| Scalability | Narrows vs TS at rat195; weak large JSP | Best gaps throughout | TSP collapse; JSP mid-tier |
| Parameter burden | High (cooling vs budget) | Moderate (tenure, list) | High (swarm + encoding) |
| Choose when… | Simple baseline; adequate TSP budget | **Quality-first** routing/scheduling | **Binary/FS wrappers**; hybrid if permutations |

### 5.7 Implementation Notes (RQ4)

**TSP:** SA T₀=3000, α=0.9995, 200 moves/temp; TS tenure 15, list 100; PSO swarm 100.  
**JSP:** SA T₀=8000, α=0.999; TS tenure 30, list 40; PSO swarm 40.  
**FS:** SA T₀=2.0, α=0.995; TS tenure 30, list 30; PSO swarm 30, w=0.6, c1=c2=1.8.

### 5.8 Limitations

1. Sample-test scale; not production benchmarks.  
2. Single frozen parameter set per domain.  
3. **TSP PSO initializer bug:** PSO ignores configured nearest-neighbor starts; TSP PSO gaps are not fair cross-algorithm evidence until fixed and rerun.  
4. **TSP tuning leakage in reporting:** Parameters tuned on eil51/berlin52/st70; only kroA100/ch130/rat195 are held-out comparison instances—TS gaps widen 6.3× tuning→held-out vs 1.3× for SA.  
5. **FS objective:** raw features (no in-fold scaling), α=0.9/β=0.1 weights; WineEW winners can sit below majority CV accuracy—narrow bands may reflect misspecification, not encoding alone.  
6. JSP job-major initializer inflates absolute gaps (relative rankings still fair).  
7. No formal significance tests yet (Wilcoxon/Friedman planned, D11).  
8. Standalone algorithms only (literature hybrids out of scope).  
9. AI-assisted development; researcher-directed protocol and interpretation.

### 5.9 Conclusion

Sample tests support **JSP as the strongest evidence**: Tabu Search leads all five held-out instances with PSO second and SA third under a clean disjoint tuning/comparison protocol. On TSP, TS wins every reported instance, but held-out gaps are much wider than tuning-set gaps (6.3× mean degradation for TS vs 1.3× for SA), and PSO routing numbers are **Unresolved** until the initializer bug is fixed. Feature selection shows a narrow objective band, but WineEW winners sit below majority CV accuracy—interpretation as an encoding finding requires objective and preprocessing revision. The Comparative Evaluation Framework maps problem properties to algorithm choice rather than declaring a single winner—consistent with the No Free Lunch principle and Pirim’s problem-dependent interpretation.

---

## 6. REFERENCES

1. Alharkan, I., et al. (2020). Tabu search and PSO for parallel machines scheduling. *Journal of King Saud University–Engineering Sciences*, 32(5), 330–338.  
2. Allvi, M. W., et al. (2020). Feature selection for learning-to-rank using SA. *IJACSA*, 11(3).  
3. Glover, F. (1989). Tabu search—Part I. *ORSA Journal on Computing*, 1(3), 190–206.  
4. Grabusts, P., et al. (2019). SA for optimal route detection. *Procedia Computer Science*, 149, 95–101.  
5. Huang, S., et al. (2016). Modified discrete PSO for flexible job-shop. *SpringerPlus*, 5, 1432.  
6. Jwo, J.-S., et al. (2023). Tabu search for manufacturing order swapping. *Engineering Proceedings*, 55(1), 51.  
7. Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization. *Proc. ICNN’95*, 1942–1948.  
8. Kirkpatrick, S., et al. (1983). Optimization by simulated annealing. *Science*, 220(4598), 671–680.  
9. Mhamdi, B., et al. (2011). Hybrid PSO-SA-TS for microwave imaging. *PIER B*, 28, 1–18.  
10. Pirim, H., et al. (2008). Tabu search: A comparative study. In *Tabu Search*, IntechOpen.  
11. Ru, S. (2024). Vehicle logistics routing via tabu search. *Scientific Reports*, 14, 11859.  
12. Sengupta, S., et al. (2019). PSO: survey and hybridization. *Machine Learning and Knowledge Extraction*, 1(1), 157–191.  
13. Talbi, E.-G. (2009). *Metaheuristics: From Design to Implementation*. Wiley.  
14. Watson, J.-P., et al. (2005). Demystifying tabu search on JSP. *JAIR*, 24, 221–261.  
15. Xie, H., et al. (2021). Enhanced PSO for feature selection. *Sensors*, 21(5), 1816.  
16. Youssef, H., et al. (2001). EA, SA, and TS: A comparative study. *Eng. Apps. AI*, 14(2), 167–181.  
17. Zhan, S.-H., et al. (2016). List-based SA for TSP. *Computational Intelligence and Neuroscience*, 2016, 1712630.  
18. Zhang, H., & Sun, G. (2002). Feature selection using tabu search. *Pattern Recognition*, 35(3), 701–711.  
19. Zhang, W., & Nicholson, C. D. (2018). Metaheuristics for slope scaling procedure. arXiv:1808.10264.  
20. Wolpert, D. H., & Macready, W. G. (1997). No free lunch theorems for optimization. *IEEE Trans. EC*, 1(1), 67–82.  
21. Hajek, B. (1988). Cooling schedules for optimal annealing. *Mathematics of Operations Research*, 13(2), 311–329.  
22. Geman, S., & Geman, D. (1984). Stochastic relaxation, Gibbs distributions, and the Bayesian restoration of images. *IEEE TPAMI*, 6(6), 721–741.  
23. Niño, F. (2012). *An Introduction to Tabu Search*. In *Nature-Inspired Algorithms for Optimisation*. Springer.

---

## APPENDIX A. Experiment Completion (2026-08-07)

| Domain | Complete | Pending |
|--------|----------|---------|
| TSP | 18/18 | — |
| JSP | 15/15 | — |
| FS | 12/12 | — |
| **Total** | **45/45** | Wilcoxon/Friedman (optional) |

Artifacts: `results/`, `results/tuning/`, `config/decisions.yaml`, `synthesis.md`.

## APPENDIX B. Pilot Test Detail (Superseded for Rankings)

| Problem | SA | TS | PSO | Budget | Runs |
|---------|----|----|-----|--------|------|
| TSP 50 cities | 581.71 | 694.37 | 1268.57 | 20k evals | 10 |
| JSP FT06 | 55.00 | 55.00 | 57.80 | 20k evals | 10 |
| FS Breast Cancer | 0.0328 | 0.0276 | 0.0338 | 2k evals | 10 |

Pilot TSP SA advantage traced to TS early plateau (candidate list 20) and corrected SA cooling spanning full budget; full protocol resolves this with list 100 and 100k evaluations across six instances.
