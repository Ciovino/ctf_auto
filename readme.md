# CTF_AUTO
automatically fetch challenges from [Molecon](https://cc-ctfd.m0lecon.it) website.

## How to run
1. Run the `./setup.sh`. It will create the virtual enviroment, intall the requirements and create a new alias for running the program.
``` bash
chmod +x setup.sh
./setup.sh
source ~/.zshrc # change here based on your shell
```
2. Run for a first time the program with the alias. The program will create a *config.ini* file. Fill it with your credentials
``` bash
new_challenge
```
3. Run the program when you need it with `new_challenge`

## Folder hierarchy
```
ctf
├── challenge_state.json    <- json file with the last update for the challenge
├── category1               <- folder for the challenges in the category1
├── category2               <- folder for the challenges in the category2
.
```

For each category:
```
category1
├── challenge1      <- folder for the challenge1
├── challenge2      <- folder for the challenge1
.
```

For each challenge:
```
challenge1
├── general_info.md     <- name, category, value, description of the challenge
├── solvers.txt         <- people who already solved the challenge 
│
└── challenge           <- folder for the challenge's file. It will contains any attachments, if any.
```

## Note
- A challenge is considered *pending* when the `['value', 'solves', 'solved_by_me']` changes. When updating a challenge, only the `general_info.md` and `solvers.txt` file are overwritten, the challenge folder does not change.
- Can only update the entire category, not single challenges. Only the pending challenges are updated.
- By default, the program will save every challenge in the `../ctf` directory, which is one level higher in the filesystem. You can change that in the [state manager creation](https://github.com/Ciovino/ctf_auto/blob/3e4ea08826fdb3fd8bde08558643ac01885c2e68/main.py#L65).
- In the `setup.sh` file, you can change the name of the [alias](https://github.com/Ciovino/ctf_auto/blob/3e4ea08826fdb3fd8bde08558643ac01885c2e68/setup.sh#L4) and the name of the [virtual enviroment](https://github.com/Ciovino/ctf_auto/blob/3e4ea08826fdb3fd8bde08558643ac01885c2e68/setup.sh#L5)