# SEO Article Generation Backend

A production-ready FastAPI backend service that generates SEO-optimized, publish-ready articles for any given topic. The system performs comprehensive SERP analysis, extracts keywords and topics, generates structured outlines aligned with search intent, and produces complete articles with SEO metadata, structured data, and strategic linking suggestions.

## Overview

This system transforms a simple topic into a fully optimized SEO article through an intelligent, multi-stage pipeline. The process begins with analyzing top search results to understand what users are actually searching for, then generates content that matches that intent. Each article includes proper heading hierarchy, keyword optimization, internal and external linking strategies, and structured data markup.

The architecture is built around an agent-based pipeline with full job persistence and resumability. If a job is interrupted at any stage, it can be resumed from the last completed step, making the system robust and suitable for production environments.

## Key Features

- **SERP-Driven Topic and Keyword Extraction**: Analyzes top 10 search results to identify primary and secondary keywords, key subtopics, and frequently asked questions
- **SEO-Aware Outline Generation**: Creates structured outlines that match true search intent based on SERP analysis
- **Full Article Generation**: Produces complete articles with proper H1/H2/H3 markup, natural keyword integration, and conversational tone
- **Internal and External Linking Strategy**: Automatically suggests relevant internal links and authoritative external references
- **Structured Data Generation**: Creates JSON-LD BlogPosting schema markup for enhanced search engine visibility
- **SEO Validation Rules**: Programmatically validates articles against SEO best practices before completion
- **Job Creation, Tracking, and Persistence**: All jobs are stored in SQLite with full state tracking
- **Crash-Safe Resumable Pipeline**: Intermediate state is stored in the database after every step, enabling recovery from any interruption

## Architecture Overview

The system is built on FastAPI, providing a modern, type-safe API interface. The core architecture follows a modular, agent-based design pattern that separates concerns and enables extensibility.

### Core Components

**FastAPI Application Layer**

- RESTful API endpoints for job creation and status retrieval
- Automatic OpenAPI documentation via Swagger UI and ReDoc
- Dependency injection for services and database sessions

**Job and Status Model**

- Jobs are persisted in SQLite using SQLAlchemy ORM
- Each job tracks its current status (pending, running, completed, failed)
- Intermediate results are stored as JSON fields, enabling full resumability

**ArticleContext Object**

- Serves as the shared state object passed through the pipeline
- Contains input parameters, SERP results, analysis, outline, and final article
- Maintains consistency across all agent stages

**Agent Pipeline**
The system uses five specialized agents, each responsible for a distinct stage:

1. **SERPAgent**: Fetches top 10 search results from SerpAPI
2. **SERPAnalysisAgent**: Extracts keywords, topics, and FAQs using OpenAI
3. **OutlineAgent**: Generates SEO-optimized article structure
4. **DraftAgent**: Writes the complete article with SEO metadata
5. **ValidationAgent**: Validates SEO constraints and plans links

**Service Layer**

- `serp_client.py`: SerpAPI integration for search result data
- `llm_client.py`: OpenAI API wrapper for content generation and analysis
- `seo_validator.py`: Programmatic SEO validation rules
- `link_planner.py`: Internal and external link suggestion logic

**SQLite Persistence**

- Lightweight, file-based database for job storage
- Enables full state recovery and job resumability
- Suitable for single-instance deployments with easy backup and portability

### Architecture Diagram

![Architecture Diagram](media/Mermaid%20Chart%20-%20Create%20complex,%20visual%20diagrams%20with%20text.-2025-12-12-165105.png)

## How the Agent Pipeline Works

The pipeline processes jobs through a sequential series of agents, each receiving and updating the shared `ArticleContext` object. This design ensures that each stage has access to all previous results while maintaining clear separation of responsibilities.

**Context Flow**

1. A new `ArticleContext` is created from the job input
2. Each agent receives the context, performs its operation, and returns an updated context
3. After each agent completes, the relevant context data is persisted to the database
4. If the job is restarted, the context is reconstructed from persisted data, and agents skip work that has already been completed

**Resumability Mechanism**

- After SERP fetch: `serp_results_json` is populated
- After analysis: `serp_analysis_json` is populated
- After outline: `outline_json` is populated
- After draft: `article_json` is populated
- After validation: `article_json` is updated with links

Each agent checks if its required input data already exists in the context. If it does, the agent skips execution, allowing the pipeline to resume from any point. This makes the system resilient to failures and suitable for background job processing.

**Error Handling**
If any agent raises an exception, the job status is updated to `failed`, the error message is stored, and the job can be inspected or retried. The persisted intermediate state ensures that completed work is never lost.

## Working Demo

The following screenshots demonstrate the system in action, showing the complete workflow from job creation to article generation.

![Job Creation](media/Screenshot%202025-12-12%20at%2010.07.45%20PM.png)

Initial job creation interface showing topic input and configuration options.

![SERP Analysis](media/Screenshot%202025-12-12%20at%2010.07.54%20PM.png)

SERP analysis results displaying extracted keywords, topics, and search intent analysis.

![Outline Generation](media/Screenshot%202025-12-12%20at%2010.08.07%20PM.png)

Generated article outline with proper heading hierarchy and section summaries.

![Article Draft](media/Screenshot%202025-12-12%20at%2010.08.28%20PM.png)

Complete article draft with markdown formatting and SEO optimization.

![SEO Metadata](media/Screenshot%202025-12-12%20at%2010.09.19%20PM.png)

SEO metadata including title tag, meta description, and keyword analysis.

![Internal Links](media/Screenshot%202025-12-12%20at%2010.09.32%20PM.png)

Suggested internal links with anchor text and target slugs.

![External References](media/Screenshot%202025-12-12%20at%2010.10.00%20PM.png)

External reference citations with context and placement suggestions.

![Structured Data](media/Screenshot%202025-12-12%20at%2010.10.33%20PM.png)

JSON-LD structured data markup for BlogPosting schema.

## API Documentation

### Create Article Job

**Endpoint:** `POST /api/v1/jobs`

Creates a new article generation job and processes it synchronously.

**Request Body:**

```json
{
  "topic": "best productivity tools for remote teams",
  "target_word_count": 1500,
  "language": "en"
}
```

**Response:**

```json
{
  "id": "a05d11c3-d7f1-43ea-9ee9-d3c0dc32eaf8",
  "input": {
    "topic": "best productivity tools for remote teams",
    "target_word_count": 1500,
    "language": "en"
  },
  "status": "completed",
  "error": null,
  "article": {
    "h1": "Best Productivity Tools for Remote Teams",
    "body_markdown": "# Best Productivity Tools for Remote Teams\n\n...",
    "seo": {
      "title_tag": "Top Productivity Tools for Remote Teams - Essential Guide",
      "meta_description": "Explore the best productivity tools for remote teams...",
      "primary_keyword": "productivity tools for remote teams",
      "secondary_keywords": ["collaboration tools", "project management", ...],
      "word_count_target": 1500,
      "estimated_word_count": 1211
    },
    "internal_links": [
      {
        "anchor_text": "SEO keyword research tools",
        "target_slug": "seo-keyword-research-tools"
      }
    ],
    "external_references": [
      {
        "title": "26 Best Collaboration Tools for Remote Teams in 2025",
        "url": "https://thedigitalprojectmanager.com/...",
        "suggested_section_slug": "benefits-of-using-productivity-tools-for-remote-teams",
        "context_reason": "Use this when discussing benefits..."
      }
    ],
    "structured_data": {
      "@context": "https://schema.org",
      "@type": "BlogPosting",
      "headline": "Best Productivity Tools for Remote Teams",
      "description": "...",
      "keywords": "..."
    }
  }
}
```

**Status Codes:**

- `201 Created`: Job created and processed successfully
- `422 Unprocessable Entity`: Invalid request body
- `500 Internal Server Error`: Processing failed (check `error` field)

### Get Job Status

**Endpoint:** `GET /api/v1/jobs/{job_id}`

Retrieves the current status and results of a job.

**Response:** Same structure as POST response above

**Status Codes:**

- `200 OK`: Job found
- `404 Not Found`: Job does not exist

**Interactive Documentation**

The API includes automatic interactive documentation:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Installation & Setup

### Prerequisites

- Python 3.11 or higher
- OpenAI API key
- SerpAPI API key

### Step-by-Step Setup

1. **Clone the repository:**

```bash
git clone <repository-url>
cd seo-engine
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Set environment variables:**

```bash
export OPENAI_API_KEY=your_openai_api_key
export SERPAPI_API_KEY=your_serpapi_api_key
```

Alternatively, create a `.env` file in the project root:

```
OPENAI_API_KEY=your_openai_api_key
SERPAPI_API_KEY=your_serpapi_api_key
```

5. **Run the application:**

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Quick Test

Test the API with curl:

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "best productivity tools for remote teams",
    "target_word_count": 1500,
    "language": "en"
  }'
```

## Example Input → Output

The following example demonstrates a complete request and response cycle. See `example_input_output.json` for the full example.

**Input Request:**

```json
{
  "topic": "best productivity tools for remote teams",
  "target_word_count": 1500,
  "language": "en"
}
```

**Output Article Structure:**

- **H1**: "Best Productivity Tools for Remote Teams"
- **Body**: Complete markdown article with multiple H2 and H3 sections
- **Word Count**: 1,211 words (within ±20% of target)

**SEO Information:**

- **Title Tag**: "Top Productivity Tools for Remote Teams - Essential Guide"
- **Meta Description**: 150-160 character description with primary keyword
- **Primary Keyword**: "productivity tools for remote teams"
- **Secondary Keywords**: 10+ related keywords extracted from SERP

**Internal Links:**

- 3+ strategically placed internal link suggestions with anchor text and target slugs
- Links are selected based on semantic relevance to article topics

**External References:**

- 2-4 authoritative external citations from top SERP results
- Each reference includes placement suggestions and context reasoning

**Structured Data:**

- JSON-LD BlogPosting schema with headline, description, and keywords
- Ready for direct integration into HTML head section

## SEO Validation Rules

The system enforces the following SEO validation rules programmatically:

### Keyword Placement

- Primary keyword must appear in the H1 heading (case-insensitive)
- Primary keyword must appear in the first 150 words of the article body
- Primary keyword must appear in at least one H2 heading (or close semantic match with 50%+ word overlap)

### Word Count Requirements

- Article word count must be within ±20% of the target word count
- Minimum: 80% of target (e.g., 1,200 words for 1,500 target)
- Maximum: 120% of target (e.g., 1,800 words for 1,500 target)

### Heading Structure

- Exactly one H1 heading in the article body
- At least 3 H2 headings for proper content hierarchy
- H3 headings are optional but recommended for detailed sections

### Link Requirements

- Minimum 3 internal link suggestions
- Minimum 2 external reference citations
- Links are validated for proper structure and relevance

### Validation Failure Handling

If any validation rule fails, the job status is set to `failed` with a detailed error message listing all violations. This ensures that only SEO-compliant articles are marked as completed.

## Design Decisions

### Agent-Based Architecture

The system uses an agent-based pipeline architecture for several key reasons:

**Modularity and Extensibility**: Each agent is a self-contained unit with a single responsibility. New agents can be added to the pipeline without modifying existing code, and agents can be reordered or conditionally executed based on requirements.

**Testability**: Agents can be tested in isolation by mocking their dependencies. The clear input-output contract (ArticleContext in, ArticleContext out) makes unit testing straightforward.

**Resumability**: By checking for existing data in the context, agents naturally support resumability. This pattern scales to more complex scenarios like parallel agent execution or conditional branching.

**Maintainability**: The separation of concerns makes the codebase easier to understand and modify. A developer working on outline generation only needs to understand the OutlineAgent, not the entire pipeline.

### Pydantic for Strict Structure

Pydantic models are used throughout the system for data validation and serialization:

**Type Safety**: Pydantic provides runtime type checking and validation, catching errors early in the development process. The integration with Python type hints enables better IDE support and static analysis.

**Serialization**: Automatic JSON serialization and deserialization simplifies database persistence and API responses. The models handle edge cases like URL validation and nested structures automatically.

**Documentation**: Pydantic models serve as living documentation of the data structures. The automatic OpenAPI schema generation in FastAPI uses these models to produce accurate API documentation.

**Evolution**: As requirements change, Pydantic models can be extended with new fields while maintaining backward compatibility through default values and optional fields.

### SQLite for Durability and Reproducibility

SQLite was chosen as the database solution for several practical reasons:

**Simplicity**: No separate database server is required. The database is a single file that can be easily backed up, versioned, or shared. This reduces deployment complexity and operational overhead.

**Durability**: SQLite provides ACID transactions and crash recovery, ensuring that job state is never lost. The WAL (Write-Ahead Logging) mode provides excellent concurrency for read-heavy workloads.

**Reproducibility**: The entire database can be included in version control or shared as a single file. This makes it easy to reproduce issues, share test data, or create demo environments.

**Performance**: For single-instance deployments with moderate load, SQLite performance is excellent. The database file can be easily migrated to PostgreSQL or MySQL if horizontal scaling becomes necessary.

**Development Experience**: Developers can inspect the database using standard SQLite tools or simple Python scripts. No database server management or connection pooling configuration is required.

### SerpAPI Instead of Direct Scraping

SerpAPI is used for search result data rather than direct web scraping:

**Reliability**: SerpAPI handles the complexities of search engine scraping, including rate limiting, CAPTCHA solving, and result parsing. This reduces the risk of IP bans or parsing failures.

**Legal Compliance**: Using an API service ensures compliance with search engine terms of service. Direct scraping can violate terms of service and lead to legal issues.

**Maintenance**: Search engine HTML structures change frequently. SerpAPI maintains the parsing logic, reducing maintenance burden on the application.

**Data Quality**: SerpAPI provides structured, normalized data that is easier to work with than raw HTML. The API handles edge cases and provides consistent data formats.

**Scalability**: SerpAPI can handle high request volumes without requiring proxy management or distributed scraping infrastructure.

## Testing

The project includes comprehensive test coverage across all major components.

### Test Structure

**Pipeline Tests** (`tests/test_pipeline.py`):

- Tests the complete agent pipeline execution
- Verifies job creation, processing, and completion
- Validates intermediate state persistence
- Ensures articles meet minimum quality requirements

**SEO Validator Tests** (`tests/test_seo_validator.py`):

- Tests all SEO validation rules individually
- Verifies error messages for failed validations
- Confirms that valid articles pass all checks
- Tests edge cases like missing keywords, insufficient word count, and improper heading structure

**API Tests** (`tests/test_api.py`):

- Tests job creation endpoint with mocked services
- Verifies job retrieval endpoint
- Tests error handling for non-existent jobs
- Uses FastAPI TestClient for integration testing

### Running Tests

Run all tests:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov=app
```

Run specific test file:

```bash
pytest tests/test_seo_validator.py
```

Run with verbose output:

```bash
pytest -v
```

### Test Coverage

The test suite covers:

- All five agents in the pipeline
- SEO validation rules (keyword placement, word count, headings, links)
- API endpoint functionality
- Error handling and edge cases
- Database persistence and state recovery

## Future Enhancements

The following enhancements are planned for future iterations:

### Background Task Queue

Implement asynchronous job processing using Celery or RQ. This would allow the API to return immediately after job creation, with status polling via the GET endpoint. This improves user experience for long-running jobs and enables better scalability.

### Revision Agent for Auto-Fixing SEO Failures

Add an agent that automatically revises articles when SEO validation fails. The agent would analyze validation errors, generate a revision prompt for the LLM, and re-validate the updated article. This would increase the success rate of article generation without manual intervention.

### Crawl4AI Integration for Full-Page Scraping

Integrate Crawl4AI to extract full page content from SERP results, not just titles and snippets. This would provide richer context for keyword extraction and outline generation, potentially improving article quality and relevance.

### Multi-Language Content Support

Extend the system to support content generation in multiple languages. This would involve:

- Language-specific SERP queries
- Localized keyword extraction
- Language-aware LLM prompts
- Locale-specific SEO best practices

### Embedding-Based Content Quality Scoring

Implement semantic similarity scoring using embeddings to evaluate article quality. Compare generated articles against top SERP results to ensure content depth and relevance. This would provide an additional quality metric beyond programmatic SEO validation.

### Advanced Link Planning

Enhance the link planner with:

- Real-time internal link database queries
- External link authority scoring (Domain Authority, PageRank)
- Contextual link placement suggestions within article body
- Link diversity analysis to avoid over-linking to single domains

## License

MIT License

Copyright (c) 2024

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
