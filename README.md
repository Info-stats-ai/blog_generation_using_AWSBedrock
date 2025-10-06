# AI Blog Generator with AWS Bedrock

> Generate AI-powered blog posts instantly using Meta's Llama 3.2 model. Just send a topic via API, get a full blog post saved to S3.

---

## What Does This Do?

Send a POST request with a blog topic → Get an AI-generated blog post → Automatically saved to AWS S3.

**Example:**
```bash
POST: {"blog_topic": "AI agents"}
Response: {"message": "Blog generated successfully", "s3_key": "blogs/AI_agents_2025-10-06_20-19-44.md"}
```

That's it. No servers to manage, no infrastructure to maintain.

---

## Why I Built This

I wanted to learn how to:
- Use large language models (LLMs) in production
- Build serverless applications on AWS
- Create REST APIs that anyone can call
- Solve real problems (content creation automation)

---

## Tech Stack

- **AWS Lambda** - Runs Python code without servers
- **Amazon Bedrock** - Provides access to Llama 3.2 AI model
- **API Gateway** - Creates the REST API endpoint
- **Amazon S3** - Stores generated blog posts
- **Python 3.13** - Lambda runtime with boto3 library

---

## Quick Start

### 1. Install Dependencies Locally

```bash
cd /Users/omkarthakur/Desktop/LLMops
python3 -m venv venv
source venv/bin/activate
pip install boto3
```

### 2. Set Up AWS Resources

**Create S3 Bucket:**
- Go to S3 Console → Create bucket
- Name: `awsbedrockinfinity`
- Region: `us-east-1`

**Request Bedrock Model Access:**
- Bedrock Console → Model access → Manage model access
- Check "Meta Llama 3.2 1B Instruct" → Request access

**Create Lambda Function:**
- Lambda Console → Create function
- Name: `awsappwithbedrock`
- Runtime: Python 3.13
- Copy `app.py` code → Deploy

**Add IAM Permissions:**

Bedrock policy:
```json
{
    "Effect": "Allow",
    "Action": ["bedrock:InvokeModel"],
    "Resource": ["arn:aws:bedrock:us-east-1::foundation-model/us.meta.llama3-2-1b-instruct-v1:0"]
}
```

S3 policy:
```json
{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject"],
    "Resource": ["arn:aws:s3:::awsbedrockinfinity/*"]
}
```

**Create API Gateway:**
- API Gateway Console → Create REST API
- Create resource: `/blog-generation`
- Create POST method → Link to Lambda
- Deploy to stage: `dev`

---

## How to Use

### API Endpoint
```
POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/blog-generation
```

### Request

```json
{
  "blog_topic": "Your topic here"
}
```

### Response (Success)

```json
{
  "message": "Blog generated successfully",
  "s3_key": "blogs/Your_topic_here_2025-10-06_20-19-44.md"
}
```

### Test with Postman

1. New POST request
2. Paste your API endpoint
3. Body → raw → JSON
4. Add: `{"blog_topic": "AI agents"}`
5. Send

---

## The Hard Parts (And How I Fixed Them)

### Problem 1: "AccessDeniedException"

**What happened:** Lambda couldn't call Bedrock.

**Why:** Missing IAM permissions.

**Fix:** 
- Added `bedrock:InvokeModel` permission to Lambda role
- Requested model access in Bedrock console

**Lesson:** AWS Bedrock needs TWO permissions - IAM policy AND model access approval.

---

### Problem 2: "Model ID not supported"

**What happened:** Used `meta.llama3-2-1b-instruct-v1:0` but got validation error.

**Why:** Llama 3.2 requires inference profile, not direct model ID.

**Fix:** Changed to `us.meta.llama3-2-1b-instruct-v1:0` (added `us.` prefix).

**Lesson:** Different models have different invocation requirements. Read the docs.

---

### Problem 3: "Extraneous key: max_tokens_to_sample"

**What happened:** Request body was rejected.

**Why:** Llama 3.2 uses `max_gen_len`, not `max_tokens_to_sample`.

**Fix:** Updated parameter name.

**Lesson:** Each model family has its own API format. Don't assume they're all the same.

---

### Problem 4: "NoSuchBucket"

**What happened:** Code referenced a bucket that didn't exist.

**Why:** Hardcoded wrong bucket name.

**Fix:** 
- Checked actual bucket name in S3 console
- Updated `s3_bucket = "awsbedrockinfinity"`
- Redeployed Lambda

**Lesson:** Always verify resource names before hardcoding them.

---

### Problem 5: Files Not Appearing in S3

**What happened:** CloudWatch logs said "success" but S3 was empty.

**Why:** Lambda role lacked S3 write permissions.

**Fix:** Added `s3:PutObject` permission to Lambda role.

**Lesson:** Lambda starts with zero permissions. Grant only what's needed (least privilege principle).

---

### Problem 6: Code Changes Not Working

**What happened:** Updated code but Lambda still ran old version.

**Why:** Forgot to click "Deploy" button.

**Fix:** Always click Deploy after editing code.

**Lesson:** Changes in Lambda console aren't live until deployed.

---

## What I Learned

### Technical Skills
- How to integrate LLMs into applications
- AWS Lambda function development
- IAM policy
