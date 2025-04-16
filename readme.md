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

## Note
- By default, the program will save every challenge in the `../ctf` directory, which is one level higher in the filesystem. You can change that in the [state manager creation](https://github.com/Ciovino/ctf_auto/blob/3e4ea08826fdb3fd8bde08558643ac01885c2e68/main.py#L65).
- In the `setup.sh` file, you can change the name of the [alias](https://github.com/Ciovino/ctf_auto/blob/3e4ea08826fdb3fd8bde08558643ac01885c2e68/setup.sh#L4) and the name of the [virtual enviroment](https://github.com/Ciovino/ctf_auto/blob/3e4ea08826fdb3fd8bde08558643ac01885c2e68/setup.sh#L5)