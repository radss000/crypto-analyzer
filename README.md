# Crypto Token Analysis Project

This project provides a comprehensive analysis of cryptocurrency tokens using a Python backend and a React frontend. It integrates TradingView technical analysis, DexScreener market data, and custom risk scoring algorithms to deliver advanced insights.

## Key Components

### Frontend
- **Framework**: React with TypeScript  
- **Build System**: Vite  

### Backend
- **Server**: Node.js with Express  
- **Analysis Module**: Python-based for crypto token analysis  
- **Token Analysis**: Asynchronous processing with multiple data sources  

---

## Core Analysis Features

The `CryptoAnalyzer` class in `crypto_analyzer.py` offers:  
- Market data retrieval from **DexScreener**  
- TradingView **technical analysis** integration  
- Custom **risk and confidence score** calculations  
- Extraction of comprehensive token metrics  

---

## Technical Indicators Calculated

- **RSI**: Relative Strength Index  
- **MACD**: Moving Average Convergence Divergence  
- **Bollinger Bands**  
- **ADX**: Average Directional Index  

---

## Risk Scoring Methodology

The risk score is calculated based on:  
- **Liquidity**  
- **24h Trading Volume**  
- **Buy/Sell Transaction Ratio**  

---

## Confidence Score Factors

The confidence score incorporates:  
- **Trading signals**  
- **Risk score**  
- **Price momentum**  

---

## Overview

This project is designed to provide comprehensive, data-driven analysis of cryptocurrency tokens. It combines advanced technical analysis and risk assessment capabilities to support informed decision-making in crypto markets.

---

## Getting Started

### Prerequisites
- Node.js
- Python 3.x
- React and TypeScript setup

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>```

2. Install dependencies:

Backend:
bash
```cd backend
npm install```
Frontend:
bash
```
cd frontend
npm install
```

Run the application:

Backend:
bash
```
npm start```

Frontend:
bash
```
npm run dev```
