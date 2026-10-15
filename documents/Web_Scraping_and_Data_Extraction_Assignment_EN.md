# Web Scraping and Data Extraction Assignment

## 1. Overview

This is a practical test designed to evaluate your ability to collect data in real-world situations, your thought process when selecting technologies, and your skills in effectively using Generative AI.

Submit your deliverables within **9 hours of the start time**, following the instructions in **Section 6: Submission Instructions**.

We will evaluate the contents that have been **committed to Git (`git commit`) by the deadline** (9 hours after the start time).

Even if you cannot complete the entire assignment within the allotted time, we will also evaluate your approach and work process. Therefore, **make sure to commit all completed work to Git before the deadline**.

## 2. Task A: Collecting Data from Company Websites

Use the following list of URLs for **10 publicly listed companies** as the input data.

Starting from each URL, follow links (crawl) to scrape data from the company's official website. Then use **Generative AI** to extract the specified information listed under **Data to Extract** below.

Each website has a different design and structure. Therefore, your program should be **highly generalizable** and able to handle a wide variety of websites.

Create a `README.md` file **in Japanese** explaining how to set up the environment and run your program.

### Target Websites

| Company | URL |
|---|---|
| Nissui (ニッスイ) | https://www.nissui.co.jp/ |
| Umios (Ｕｍｉｏｓ) | https://www.umios.com/ |
| Yukiguni Factory (ユキグニファクトリー) | https://www.yukiguni-factory.co.jp/ |
| Sakata Seed (サカタのタネ) | https://www.sakataseed.co.jp/ |
| Hokuto (ホクト) | https://www.hokto-kinoko.co.jp/ |
| Sho-Bond Holdings (ショーボンドホールディングス) | https://www.sho-bondhd.jp/ |
| Mirait One (ミライト・ワン) | https://www.mirait-one.com/ |
| Tama Home (タマホーム) | https://www.tamahome.jp/ |
| Kyokuyo (極洋) | https://www.kyokuyo.co.jp/ |
| Nihon Aqua (日本アクア) | https://www.n-aqua.jp/ |

### Data to Extract

For each company, extract the following information:

1. **Head office address**
2. **Representative's name**
3. **Capital**
4. **Year and month of establishment**

## 3. Task B: Challenge — Websites with Anti-Bot Protection (Optional)

**Only attempt this task if you have fully completed Task A.**

The target page below blocks access using common web scraping methods. Try to retrieve data from this website.

**Target page:** https://vn.indeed.com/jobs?q=remote

In `report.md`, describe both of the following:

1. **Anti-bot measures:** What types of anti-bot protection are implemented on the target page?
2. **Attempts and results:** What approaches or methods did you try in response to those anti-bot measures, and what were the results?

## 4. Technology Selection and Comparison of Approaches

Consider and compare multiple approaches for retrieving the data, such as different libraries, frameworks, no-code tools, and the use of Generative AI APIs.

**Examples:**

- Python + Playwright + LangChain
- TypeScript + Firecrawl + Vercel AI SDK
- Dify
- n8n

*These are examples of tools and products.*

Evaluate each approach using the following three criteria. Document your evaluation and the reasons for your final selection in `report.md`.

| Criterion | What to Evaluate |
|---|---|
| **Cost** | Development time, infrastructure costs, tool usage fees, etc. |
| **Speed** | Development speed and execution speed of data collection |
| **Quality / Completeness** | Accuracy of the extracted data and minimizing missing or overlooked information |

## 5. Use of Generative AI

You are free to use Generative AI tools such as **ChatGPT, Claude, and GitHub Copilot** for this assignment.

However, you must comply with the following requirement:

> **Mandatory:** If you use a conversational AI tool such as ChatGPT or Claude, you must submit the history of your prompts and the AI's responses **or a shareable link to that conversation**.

## 6. Submission Instructions

Submit **all deliverables** (source code, data, documentation, etc.) through **GitHub**.

1. **Create a repository:** Create a **private GitHub repository**.
2. **Grant access:** Invite the following GitHub user as a collaborator: `atsunori0406`.
3. **Recommended directory structure:** Organize the repository as shown below. Use the **English folder and file names exactly as shown**.

```text
├── prompts/       # History of prompts used with Generative AI (TXT format)
├── result/        # Collected data (CSV or JSON format)
├── src/           # All source code developed for the assignment
├── README.md      # Environment setup and execution instructions
└── report.md      # Technology comparison table and findings from Task B
```
