# SEMu Symbolic Execution-based Mutant Analysis Framework

SEMu (KLEE-SEMu) is a (Dynamic) Symbolic Execution-based Mutant analysis framework build on top of [KLEE](https://github.com/klee/klee) Symbolic Virtual Machine. 

SEMu uses a form of differential symbolic execution to generate test inputs to kill mutants. The relevant paper can be found [here](https://orbilu.uni.lu/bitstream/10993/44339/1/main%20%283%29.pdf) (the paper's pdf [here](https://orbilu.uni.lu/bitstream/10993/44339/1/main%20%283%29.pdf) and the data-set [here](https://github.com/thierry-tct/SEMu-Experiement-data)), and cited as following:

``` 
[x] Thierry Titcheu Chekam, Mike Papadakis, Maxime Cordy, Yves Le Traon. Killing Stubborn Mutants. 
     ACM Transactions on Software Engineering and Methodology.  January 2021. 
     Article No.: 19. https://doi.org/10.1145/3425497
```

SEMu is easily used with the [Muteria](https://github.com/muteria/muteria) Framework and generate test to kill mutants generated by the [Mart](https://github.com/thierry-tct/mart) mutation tool. 

---

## TABLE OF CONTENTS
- [SEMu Symbolic Execution-based Mutant Analysis Framework](#semu-symbolic-execution-based-mutant-analysis-framework)
  - [TABLE OF CONTENTS](#table-of-contents)
  - [BUILDING](#building)
    - [A. Using pre-build Docker image](#a-using-pre-build-docker-image)
    - [B. Build from Source](#b-build-from-source)
  - [USAGE](#usage)
    - [A. Description of SEMu Specific Arguments](#a-description-of-semu-specific-arguments)
      - [1. Main arguments](#1-main-arguments)
      - [2. Tuning arguments of Main arguments](#2-tuning-arguments-of-main-arguments)
      - [3. Other arguments](#3-other-arguments)
    - [B. Description of Required KLEE arguments and values, when running SEMu](#b-description-of-required-klee-arguments-and-values-when-running-semu)
    - [C. Description of the Required LLVM bitcode file format](#c-description-of-the-required-llvm-bitcode-file-format)
    - [D. Examples](#d-examples)
      - [1. Without using seeds](#1-without-using-seeds)
      - [2. Using seeds](#2-using-seeds)
  - [MAINTENANCE](#maintenance)
    - [A. SEMu Relevant code](#a-semu-relevant-code)
    - [B. Updating SEMu](#b-updating-semu)
  - [CONTRIBUTORS](#contributors)

## BUILDING

### A. Using pre-build [Docker](https://www.docker.com/) image
This tool has a Docker image available here [https://hub.docker.com/r/thierrytct/klee-semu](https://hub.docker.com/r/thierrytct/klee-semu).
Start the Docker container in interactive mode with the following command:
```bash
sudo docker run -it --rm thierrytct/klee-semu:llvm-3.4.2 bash
```

The `Dockerfile` used to build SEMu's Docker image is found in the code location `lib/Mutation/Dockerfile`.

### B. Build from Source

Follow the procedure of KLEE to build from source. The procedure using _configure/make_ is available [here](http://klee.github.io/releases/docs/v1.3.0/build-llvm34/). The procedure using _cmake_ is available [here](http://klee.github.io/releases/docs/v1.4.0/build-llvm34/).

## USAGE
The usage of SEMu is similar to that of KLEE. For integration with other testing tools and/or perform automated test execution, consider using [Muteria](https://github.com/muteria/muteria) (find some examples [here](https://github.com/muteria/example_c)).

The command line is of this form:
``` bash
klee-semu <KLEE and SEMu specific control arguments> \
          <LLVM bitcode (.bc) file> \
          <Optional Symbolic arguments>
```

### A. Description of SEMu Specific Arguments

#### 1. Main arguments
These are the 7 main arguments described in the SEMu paper.

| Argument | Type | Description |
| -------- | :----: | ----------- |
| --semu-precondition-length | value | The Precondition Length (PL) whose value is an integer >= 0, or value -1 for GMD2MS or value -2 for SMD2MS. |
| --semu-checkpoint-window | value | The Checkpoint Window (CW) whose value is an integer >= 0. |
| --semu-propagation-proportion | value | Propagation Proportion (PP) whose value is a real number in the interval [0, 1]. |
| --semu-MDO-propagation-selection-strategy | boolean | Propagation Selection Strategy (PSS) set to Minimum Distance to Output (MDO). By default, Random strategy (RND) is used. Note that this is used only if PP is neither 0 nor 1. |
| --semu-minimum-propagation-depth | value | The Minimum Propagation Depth (MPD) whose value is an integer >= 0. |
| --semu-no-state-difference | boolean | No State Difference (NSD) disables state comparison for test generation. |
| --semu-number-of-tests-per-mutant | value | The Number Of Tests Per Mutant (NTPM) whose value is the maximum number of tests to generate per mutants. | 


#### 2. Tuning arguments of Main arguments
These arguments affect how the values of some main arguments are interpreted, for more flexibility. 

| Argument | Type | Description |
| -------- | :----: | ----------- |
| --semu-use-basicblock-for-distance | boolean | This argument enable the use of the number of basic blocks as distance for the Minimum Distance to Output (MDO) strategy. By default, the number of statements is used. |
| --semu-use-only-multi-branching-for-depth | boolean | This argument enable to only count the branching points where both branches are feasible when calculating the checkpoint Window (CW). By default, all branching points are used. |
| --semu-no-environment-output-diff | boolean | This argument disables the consideration of calls to the output environment (library calls that changes the environment, like _printf_ for example) when comparing states at the checkpoints. | 
| --semu-max-total-tests-gen | value | This argument sets the total number of tests to generate across all mutants. Setting this to an integer > 0 invalidate the NTPM argument such that the maximum number of test per mutant is not fixed anymore. |
| --semu-custom-output-function | value | Specify the functions to consider as output functions, besides the standard ones. Specify this multiple times for multiple functions. |

#### 3. Other arguments
These are arguments that were added do to extra stuffs.

| Argument | Type | Description |
| -------- | :----: | ----------- |
| --semu-disable-post-mutation-check | boolean | This argument disable the conservative path pruning. With this enabled, SEMu would not check for infection to discard non infected states. This is important for higher order mutation. Make sure to enable this to generate tests inputs for higher order mutants. |
| --semu-testsgen-only-for-critical-diffs | boolean | This argument enable to generate tests only for state difference that are severe (these do not include variable values difference) |
| --semu-forkprocessfor-segv-externalcalls | boolean | This argument enable SEMu to create a ne process when making a system call, to avoid the whole execution to be stopped due to an exception in the system call execution. This happens which invalid calls to _printf_ (when the string format does not match with the values given). |
| --semu-no-error-on-memory-limit | boolean | This argument allows SEMu to discard states, without an error, when the specified memory limit is exceeded. note that the states are discarded randomly. Not setting this enable to ensure that no state is discarded randomly, due to memory limit. |
| --semu-candidate-mutants-list-file | value | This argument specify a file that contains a new line-separated list of mutants ID to consider for test generation. This is important to filter the mutants and generate test only for the few specified mutants. This can also be useful, if there are too many mutants, to split the test generation in rounds (example 10 mutants per round). |
| --semu-quiet | boolean | This argument, when set, suppress extra log when running SEMu. | 
| --semu-loop-break-delay | value | This argument stops SEMu from staying on a loop forever, by giving the amount of time it should stay exploring a loop. Once the time is exceeded, the paths that stay in the loop are pruned. The specified value is the time in seconds. |

### B. Description of Required KLEE arguments and values, when running SEMu

These KLEE arguments and the specified values are required to be set when running SEMu.
- `--search bfs`

In _seeding_ mode (When using seeds), the following must additionally be set: 
- `--only-replay-seeds`
- `--seed-out-dir <path-to-seed_dir>`

_Note (for maintenance - TODO) that for the newer version of KLEE, `--seed-out-dir` is changed to `seed-dir`._

### C. Description of the Required LLVM bitcode file format

The LLVM bitcode file must contain the following:

- The mutants IDs must go from _1_ to _N_, where _N_ is the number of mutants.
- The module must contain a mutant ID selector global variable, named `klee_semu_GenMu_Mutant_ID_Selector`, which is a 32 bit integer (`i32` in LLVM).
- The mutant ID selector needs to be initialized to the highest mutant ID + 1 (_N_ + 1). This is so that a direct execution will execute the original program (Mutant ID varaible not corresponding to any mutant).
- The mutants need to be represented using a `switch` statement controlled by the mutant ID global variable.
- There must be a declaration of the selection function function named`klee_semu_GenMu_Mutant_ID_Selector_Func`, which takes two mutant IDs as arguments (two `i32` values), representing a range of mutant IDs, and returns `void`.
- Right before any mutant selection `switch` statement, there must be calls to the selection function `klee_semu_GenMu_Mutant_ID_Selector_Func` where the arguments represent the range of mutants ID present in the `switch` statement. In case the IDs are not continuous, make multiple consecutive calls to `klee_semu_GenMu_Mutant_ID_Selector_Func` for each interval. e.g. make two calls with (4,6) and (8,8) as arguments, respectively, if the mutants in the corresponding `switch` statement are with IDs 4, 5, 6 and 8.
- If `--semu-disable-post-mutation-check` is not used, there must be a declaration of the post mutant function `klee_semu_GenMu_Post_Mutation_Point_Func`, which is similar in signature with `klee_semu_GenMu_Mutant_ID_Selector_Func`, but instead of being called before the mutant, is called right after the mutants.
- If `--semu-disable-post-mutation-check` is not used, there must be call to the function `klee_semu_GenMu_Post_Mutation_Point_Func` right after the corresponding mutants. This enable SEMu to do conservative pruning and remove the mutant states that are uninfected (same as corresponding original ones). Note that each mutant point's `klee_semu_GenMu_Post_Mutation_Point_Func` mush also have the call for the original program as following `klee_semu_GenMu_Post_Mutation_Point_Func(0,0)`.

Here is an example of Meta-mutant code that is expected by SEMu. This is represented in C for simplicity and can be compiled to LLVM for use with SEMu.

Initial code:
```C
#include <stdio.h>
#include <stdlib.h>
int main (int argc, char ** argv) {
    int x = atoi(argv[1]);
    if (x > 0) {
        x = x + 10;
        printf ("Changed\n");
    }
    printf ("DONE!\n");
    return x;
}
```

After creating 4 mutants, such that Mutant 1 changes `x = x + 10` into `x = x - 10`, mutant 2 changes `x = x + 10` into `x = 10`, mutant 3 deletes the statement `printf ("DONE!\n")`, and mutant 4 deletes the statement `x = x + 10`. The meta mutant file will be following:

``` C
#include <stdio.h>
#include <stdlib.h>

// Mutant ID selector global initialized to N+1 (N=4)
unsigned long  klee_semu_GenMu_Mutant_ID_Selector = 5;

// mutant ID selector function. SEMu forks mutant states 
// at calls to this
void klee_semu_GenMu_Mutant_ID_Selector_Func (unsigned long fromID, unsigned long toID);

// mutated code successor code. First code after mutant code.
// This is used by SEMu to do conservative pruning 
// of no infection
void klee_semu_GenMu_Post_Mutation_Point_Func (unsigned long fromID, unsigned long toID);

int main (int argc, char ** argv) {
    int x = atoi(argv[1]);
    if (x > 0) {
        klee_semu_GenMu_Mutant_ID_Selector_Func(1,2);
        klee_semu_GenMu_Mutant_ID_Selector_Func(4,4);
        switch (klee_semu_GenMu_Mutant_ID_Selector) {
            case 1: x = x - 10; break;
            case 2: x = 10; break;
            case 4: break;
            default: x = x + 10;
        }
        klee_semu_GenMu_Post_Mutation_Point_Func(0,0);
        klee_semu_GenMu_Post_Mutation_Point_Func(1,2);
        klee_semu_GenMu_Post_Mutation_Point_Func(4,4);
        printf ("Changed\n");
    }
    klee_semu_GenMu_Mutant_ID_Selector_Func(3,3);
    switch (klee_semu_GenMu_Mutant_ID_Selector) {
        case 3: break;
        default: printf ("DONE!\n");
    }
    klee_semu_GenMu_Post_Mutation_Point_Func(0,0);
    klee_semu_GenMu_Post_Mutation_Point_Func(3,3);
    return x;
}
```

### D. Examples
Assuming that we have an example program named `example.c` and that was compiled into LLVM bitcode to produce `example.bc` file as following:
```
clang -g -c -emit-llvm example.c -o example.bc
```
Then [Mart](https://github.com/thierry-tct/mart) was used to generate the meta mutant file for SEMu, named `example.MetaMu.bc`, as following:
```
mart example.bc
```
The file `example.MetaMu.bc` is located into the folder `mart-out-0`.

Following are example of commands. 

#### 1. Without using seeds

``` bash
klee-semu \
  --allow-external-sym-calls \
  --posix-runtime \
  --semu-no-error-on-memory-limit \
  --solver-backend z3 \
  --max-memory 2048 \
  --max-time 300 \
  --libc uclibc \
  --search bfs \
  --semu-precondition-length 0 \
  --semu-checkpoint-window 1 \
  --semu-propagation-proportion 0.25 \
  --semu-minimum-propagation-depth 1 \
  --semu-number-of-tests-per-mutant 1 \
  example.MetaMu.bc --sym-arg 4
```

#### 2. Using seeds

Need to specify the directory that contains the seeds (assuming `example_path/seeds_dir` for this example) and `--only-replay-seeds`. The seeds can be created by running KLEE first. The output of KLEE (the `.ktest` files) can be used as seeds for SEMu.

``` bash
klee-semu \
  --allow-external-sym-calls \
  --posix-runtime \
  --semu-no-error-on-memory-limit \
  --solver-backend z3 \
  --max-memory 2048 \
  --max-time 300 \
  --libc uclibc \
  --search bfs \
  --semu-precondition-length 0 \
  --semu-checkpoint-window 1 \
  --semu-propagation-proportion 0.25 \
  --semu-minimum-propagation-depth 1 \
  --semu-number-of-tests-per-mutant 1 \
  --only-replay-seeds \
  --seed-out-dir example_path/seeds_dir
  example.MetaMu.bc --sym-arg 4
```

## MAINTENANCE

### A. SEMu Relevant code

The main components added in KLEE to create SEMu are located in in the code in `lib/Mutation` (mainly the source code files `ExecutionState_KS.h`, `ExecutionState_KS.cpp`, `Executor_KS.h`, and `Executor_KS.cpp`), and `tools/klee-semu` (mainly the source code file `klee-semu.cpp`).

### B. Updating SEMu

This tool need to be integrated into newer versions of KLEE. The master branch correspond to the master branch of klee. For each use version of klee, the branch `semu-klee-<version>` corresponding to SEMu ported to the version `<version>` of KLEE.
Update the master branch from the [KLEE](https://github.com/klee/klee) repository and update the tags as following (assuming that the git remote `klee` was added as following `git remote add klee https://github.com/klee/klee.git`):
```
git checkout master
git pull klee master
git push

git fetch --tags klee master
git push origin --tags

```

After SEMu is ported to a newer version of klee, set the default branch of the remote SEMu repository to the newest `semu-klee-<version>` branch

## CONTRIBUTORS

[Thierry Titcheu Chekam](https://github.com/thierry-tct)
