#!/usr/bin/env bash
set -e

##########################
# Prerequisites:
#  - git
#  - npm (or yarn)
#  - python3 + pip
##########################

# Check for Node.js and npm
if ! command -v node &> /dev/null || ! command -v npm &> /dev/null; then
    echo "❌ Node.js and/or npm not found!"
    echo "Please install Node.js from https://nodejs.org/"
    echo "This will automatically install npm."
    exit 1
fi

# 1. Install OpenZeppelin contracts for Solidity imports
if [ -d "node_modules/@openzeppelin/contracts" ]; then
  echo "📦 @openzeppelin/contracts already installed"
else
  echo "📥 Installing @openzeppelin/contracts via npm..."
  npm init -y >/dev/null 2>&1
  npm install @openzeppelin/contracts
fi

# 2. Clone (or update) the Account-Abstraction reference repo
AA_DIR="account-abstraction"
if [ -d "$AA_DIR" ]; then
  echo "📂 $AA_DIR already exists; pulling latest changes..."
  git -C "$AA_DIR" pull
else
  echo "🔄 Cloning Account-Abstraction repo..."
  git clone https://github.com/eth-infinitism/account-abstraction.git "$AA_DIR"
fi

# 3. (Optional) Copy only the relevant folders into your project structure
#    adjust paths if your contracts live elsewhere
echo "🗂 Copying AA contracts into src/contracts/"
mkdir -p src/contracts
cp -r "$AA_DIR"/contracts/interfaces    contracts/
cp -r "$AA_DIR"/contracts/core          contracts/
cp -r "$AA_DIR"/contracts/utils         contracts/



# 4. Install Python toolchain for Vyper & Web3.py
echo "🐍 Installing Python dependencies..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing uv..."
    pip install uv
fi

uv sync

echo "✅ Setup complete!"
