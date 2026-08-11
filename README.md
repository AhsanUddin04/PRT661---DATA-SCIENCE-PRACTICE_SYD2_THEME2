# Australian House Price Forecasting

## PRT661 Data Science Practice - Assessment 1

### Project Overview

This project focuses on predictive analytics and time-series forecasting for the Australian residential real estate market.

The project aims to develop a data science pipeline that combines government property-sales data with Australian Bureau of Statistics (ABS) benchmark statistics to investigate and forecast short-term dwelling-price changes at the state and suburb levels.

The project is designed under Theme 2, which focuses on regression and time-series analysis.

---

## Project Objectives

The main objectives of the project are to:

- Acquire publicly available Australian property-sales and housing data.
- Store and manage the collected data using an appropriate database system.
- Process and prepare the data for analysis.
- Apply statistical and machine-learning forecasting techniques.
- Identify important property, regional and time-related characteristics.
- Develop visualisations to communicate historical trends and forecasts.
- Present forecast uncertainty to help users interpret predictions responsibly.

---

## Problem Statement

Property prices do not change uniformly across Australia. Different states, regions and suburbs can experience significantly different price movements.

There is a need for an accessible and transparent approach that uses publicly available government data to analyse historical property trends and provide short-term forecasts.

This project investigates whether government property-sales data, combined with ABS information, can be used to predict dwelling-price changes one to four quarters ahead with an acceptable level of accuracy.

---

## Data Sources

The project will primarily use publicly available government data.

### Primary Data Source

- State government property-sales open data, with the NSW Valuer General data used as the initial pilot source.

### Supporting Data Sources

- Australian Bureau of Statistics (ABS) Total Value of Dwellings.
- Archived ABS Residential Property Price Indexes (RPPI).

The state government property-sales data provides more granular property-level information, while ABS data provides broader housing-market benchmarks and historical context.

---

## Planned Data Science Pipeline

The project follows a structured data science workflow:

```text
Data Acquisition
       ↓
Data Storage
       ↓
Data Processing
       ↓
Exploratory Data Analysis
       ↓
Feature Engineering
       ↓
Forecasting / Machine Learning
       ↓
Evaluation
       ↓
Visualisation
       ↓
End Users

---

## Planned Architecture

The planned architecture uses open-source technologies throughout the main project.

### Data Acquisition
- Python
- Requests
- Pandas

### Data Storage
- PostgreSQL

### Data Processing
- Python
- Pandas

### Forecasting and Machine Learning
- Statsmodels
- Prophet
- Scikit-learn

### Visualisation
- Plotly Dash

The architecture is designed to support a reproducible data science workflow from government data acquisition through processing, forecasting and visualisation.

---

## Project Workflow

The project follows an iterative CRISP-DM-style workflow.

The planned workflow includes:

1. Business and project understanding
2. Data acquisition
3. Data understanding
4. Data preparation
5. Exploratory data analysis
6. Feature engineering
7. Forecasting and model evaluation
8. Visualisation and reporting

The workflow will be managed through Jira, while project code and documentation will be maintained in GitHub.

---

## Team Members

| Team Member | Role |
|---|---|
| Ahsan Uddin | Project Lead / Data Acquisition |
| Ferdous Anwar Anik | Data Engineer |
| Mohd Yah-Ya Raiyan | Data Analyst |
| Abrar Bin Khaiyum | Visualisation & Documentation Lead |

### Team Responsibilities

**Ahsan Uddin**
- Project coordination
- Jira and GitHub management
- Data acquisition planning

**Ferdous Anwar Anik**
- Database design
- Data storage planning
- Data cleaning pipeline

**Mohd Yah-Ya Raiyan**
- Exploratory data analysis
- Feature engineering
- Data analysis

**Abrar Bin Khaiyum**
- Visualisation planning
- Dashboard planning
- Project documentation

---

## Project Management

Jira is used to manage project tasks, team responsibilities and weekly progress.

GitHub is used for:

- Source code
- Documentation
- Data-source records
- Project collaboration
- Version control

---

## Current Stage

This repository is currently being developed as part of **PRT661 Data Science Practice - Assessment 1: Project Proposal and Design**.

Assessment 1 focuses on validating:

- Project feasibility
- Project planning
- Architecture design
- Workflow design
- Role allocation
- Theme alignment
- Risk and ethical considerations

The forecasting models, dashboard and other implementation components are planned for later stages of the project.

---

## Risk and Governance

Key project risks include:

- Limited generalisability when initially using a single-state dataset.
- Potential errors or non-arm's-length property-sale records.
- Structural changes in the housing market.
- Uneven contribution among team members.

The project will use documented data sources, version-controlled code and reproducible project requirements.

Forecast results will be presented with appropriate uncertainty information to reduce the risk of misleading users.

---

## References

Australian Bureau of Statistics. (2026). *Total value of dwellings*. https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/total-value-dwellings

Australian Bureau of Statistics. (2021). *Residential property price indexes: Eight capital cities (archived)*. https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/residential-property-price-indexes-eight-capital-cities

NSW Government. (2026). *How to find property sales information*. https://www.nsw.gov.au/housing-and-construction/land-values-nsw/how-to-find-property-sales-information
