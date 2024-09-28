# Tutor Service

<div align="center">

![GitHub Workflow Status (with event)](https://img.shields.io/github/actions/workflow/status/SverreNystad/TutorAI/django.yml)
![GitHub top language](https://img.shields.io/github/languages/top/SverreNystad/TutorAI)
![GitHub language count](https://img.shields.io/github/languages/count/SverreNystad/TutorAI)
[![Project Version](https://img.shields.io/badge/version-1.0.0-blue)](https://img.shields.io/badge/version-1.0.0-blue)

<img src="docs/images/TutorAI.png" width="50%" alt="Cogito Image" style="display: block; margin-left: auto; margin-right: auto;">
</div>

<details> 
<summary><b>📋 Table of contents </b></summary>

- [Tutor Service](#tutor-service)
  - [Introduction](#introduction)
    - [Features](#features)
  - [Quick Start](#quick-start)
    - [Prerequisites](#prerequisites)
    - [Clone the repository](#clone-the-repository)
    - [Configuration](#configuration)
    - [Usage](#usage)
  - [📖 Documentations](#-documentations)
  - [Contributors](#contributors)

</details>

## Introduction
Tutor-Service is the main service of the TutorAI Procject. It encompasses the main educational functionalities such as flashcard generation, test generation, and source finding.

### Features
Tutor-Service offers a comprehensive set of features to enhance the learning experience:

- **Information search**: Retrieve relevant citations and incorporate them into responses to user questions. This ensures comprehensive, accurate, and well-cited information, enhancing the learning process.
- **Flashcards and Memory aids**: Enhance memory retention with customizable digital flashcards, exportable to Anki and Quizlet.
- **Quiz and test generation**: Automatically generate quizzes and tests based on the uploaded material.
- **Quiz and test grading**: Receive automatic grading and feedback on quizzes and tests to track progress and identify improvement areas.
- **Compendium**: Generate a summary of the uploaded material, making it easier to review and understand the content.
- **Study streaks**: Motivate regular engagement with learning material through gamified elements, making education a daily habit, and exams passed easily.

## Quick Start

### Prerequisites
- Ensure that git is installed on your machine. [Download Git](https://git-scm.com/downloads)
- Docker is used for the backend and database setup. [Download Docker](https://www.docker.com/products/docker-desktop)

### Clone the repository

```bash
git clone https://github.com/The-TutorAI-project/tutor-service.git
cd TutorAI
```

### Configuration
Create a `.env` file in the root directory of the project and add the following environment variables:

```bash
OPENAI_API_KEY = 'your_openai_api_key'
MONGODB_URI = 'your_secret_key'
```

Optionally, you can add the following environment variables to customize the project:

```bash
GPT_MODEL = 'gpt-3.5-turbo' # OpenAI model to use
```


### Usage
To start Tutor-Service, run the following command in the root directory of the project:

```bash
docker compose up --build
```

To access the backend, navigate to `http://localhost:8000` in your browser.

## 📖 Documentations

- [Developer Setup Guild](docs/manuals/setup)
- [Testing](docs/manuals/testing.md)
- [Architecture](docs/architecture/architectural_design.md)




