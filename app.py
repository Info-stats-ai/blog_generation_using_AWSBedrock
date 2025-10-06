import boto3   # AWS SDK for Python, lets us talk to AWS services like Bedrock and S3
import botocore.config   # Extra config options for boto3 (timeouts, retries, etc.)
import json   # To encode/decode data to/from JSON (Bedrock needs JSON input/output)
import datetime   # Used to generate timestamps for S3 file naming

# Function: Generate a blog using Amazon Bedrock with Llama 3.2
def blog_generate_using_bedrock(blogtopic: str) -> str:
    prompt = f"Write a detailed blog on the topic '{blogtopic}' in markdown format."
    # This is the actual instruction we send to the model. f-string inserts the topic dynamically.

    body = {
        "prompt": prompt,  
        # The model expects the text prompt here.
        "max_gen_len": 1024,  
        # Max tokens the model should generate (Llama 3.2 uses max_gen_len instead of max_tokens_to_sample).
        "temperature": 0.7,  
        # Controls randomness/creativity (higher → more creative, lower → more factual).
        "top_p": 0.95,  
        # Nucleus sampling (helps control diversity of words).
    }

    try:
        # Create Bedrock client
        bedrock = boto3.client(
            "bedrock-runtime",  # Service name for Bedrock Runtime API
            region_name="us-east-1",  # Region where Bedrock is available (must match your access region).
            config=botocore.config.Config(
                read_timeout=60,  # Max time to wait for a response from model (60s).
                max_pool_connections=5000,  # Max network connections (helps Lambda handle multiple requests).
                retries={"max_attempts": 3}  # Retry up to 3 times if request fails (network issues, etc.).
            )
        )

        # Call the Bedrock model
        response = bedrock.invoke_model(
            body=json.dumps(body),  # Convert Python dict → JSON string for the request body.
            modelId="us.meta.llama3-2-1b-instruct-v1:0",  # Using inference profile for Llama 3.2 1B Instruct.
            accept="application/json",  # Format of response we expect from Bedrock.
            contentType="application/json"  # Format of the request body we are sending.
        )

        # Read response body (stream) and convert back to Python dict
        response_content = response["body"].read().decode("utf-8")  
        # Raw response is a byte stream, so we decode it into text.
        response_data = json.loads(response_content)  
        # Convert JSON string back into Python dict.

        # Extract model's generated text
        blog_details = response_data.get("generation", "")  
        # Bedrock Llama returns generated text inside the "generation" field.
        return blog_details

    except Exception as e:
        print(f"Error: {e}")  # Print the error to CloudWatch Logs (for debugging).
        return "Error in generating blog"  # Return fallback text if something goes wrong.

# Function: Save the generated blog to S3
def save_blog_details_s3(s3_bucket, s3_key, generate_blog) -> bool:
    s3 = boto3.client("s3")  # Create an S3 client to talk to Amazon S3 service.
    try:
        s3.put_object(
            Bucket=s3_bucket,  # Name of the S3 bucket where we want to store the blog.
            Key=s3_key,  # Path (folder + filename) inside the bucket.
            Body=generate_blog.encode("utf-8")  # Blog text must be converted to bytes before uploading.
        )
        print(f"✅ Blog saved to S3 bucket '{s3_bucket}' with key '{s3_key}'")  # Log success message to CloudWatch.
        return True
    except Exception as e:
        print(f"S3 Error: {e}")  # Log error if S3 upload fails.
        return False

# Lambda entry point
def lambda_handler(event, context):
    try:
        # Parse incoming request body
        event = json.loads(event["body"])  
        # Lambda gets event as JSON string, so we parse it to dict.
        blogtopic = event.get("blog_topic", "AI and Technology")  
        # Extract the blog topic, use default if missing.

        # Generate blog from Bedrock
        generate_blog = blog_generate_using_bedrock(blogtopic)  
        # Call function above to get model-generated blog.

        if generate_blog and "Error" not in generate_blog:
            current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  
            # Get current timestamp for unique file naming.
            s3_key = f"blogs/{blogtopic.replace(' ', '_')}_{current_time}.md"  
            # Build S3 key (filename) with blog topic + timestamp.
            s3_bucket = "awsbedrockinifinity"  
            # Changed to existing bucket name.

            save_blog_details_s3(s3_bucket, s3_key, generate_blog)  
            # Save generated blog to S3.

            return {
                "statusCode": 200,  # HTTP 200 = Success
                "body": json.dumps({
                    "message": "Blog generated successfully",  
                    "s3_key": s3_key  # Return S3 file path so caller knows where blog is stored.
                })
            }
        else:
            return {
                "statusCode": 500,  # HTTP 500 = Server error
                "body": json.dumps({"message": "Blog generation failed"})  # Response if blog generation didn’t work.
            }

    except Exception as e:
        print(f"Lambda error: {e}")  # Log any unexpected errors in CloudWatch.
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Lambda error: {str(e)}"})  # Send back error message in response for debugging.
        }
