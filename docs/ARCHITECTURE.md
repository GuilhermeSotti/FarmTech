# FarmTech Architecture

## Overview

FarmTech is a modular application divided into 5 main phases:

1. Area Calculation
2. Model Training
3. IoT Simulation
4. Dashboard
5. Computer Vision

## System Components

- FastAPI Backend
- PostgreSQL Database
- AWS Services (SQS, S3)
- Machine Learning Models
- IoT Simulators

## Data Flow

1. Area calculation inputs
2. Model training with historical data
3. IoT data collection
4. Real-time dashboard updates
5. Vision processing pipeline

## Infrastructure

The application is containerized using Docker and deployed using infrastructure as code (Terraform).
