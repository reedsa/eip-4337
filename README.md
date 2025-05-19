# EIP-4337 Example

A development CLI to provide a basic understanding of account abstraction.

This tool provides a workflow that creates a smart wallet account and send operations on a user's behalf. The user is guided through steps to initialize accounts and contracts required for user operations to succeed.


### Getting started

Initialize the project and install required dependencies.

#### Prerequisites

pip or uv is required to sync Python dependencies.

npm is optional but recommended.

#### Install dependencies

##### Install script

As a convenience, a script is available to quickly install everything.

:warn: npm must be installed prior to running the script. See https://nodejs.org/ to get the latest version.

```sh
./source/install_deps.sh
```

##### Manual install
Or, if you'd like to install everything yourself:

Install Python packages
```sh
uv sync
```

Or via pip into a virtual environment
```sh
pip install .
```

Install OpenZeppelin contracts
```sh
# Either via npm (recommended) …
npm init -y
npm install @openzeppelin/contracts

# … or by cloning their repo
# git clone https://github.com/OpenZeppelin/openzeppelin-contracts.git
# cp -r openzeppelin-contracts/contracts/utils ./node_modules/@openzeppelin/contracts/utils
```

Clone the account-abstraction repo and copy the Solidity contracts into the contracts folder
```sh
# Clone the AA repo
git clone https://github.com/eth-infinitism/account-abstraction.git

# Copy only the folders you need into your project
mkdir -p src/contracts
cp -r account-abstraction/contracts/interfaces    src/contracts/
cp -r account-abstraction/contracts/core          src/contracts/
cp -r account-abstraction/contracts/utils         src/contracts/
```

#### Install CLI globally

```sh
uv tool install . -e
```

### Run the tool

#### Setup local node with Anvil

```sh
anvil -code-size-limit 200000
```

#### Run the CLI

Ensure you are in the project directory and run:

```sh
eip4337
```
