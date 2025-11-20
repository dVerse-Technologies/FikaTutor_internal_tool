import json
import logging
import os
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


def validate_json_structure(data: Dict[str, Any]) -> str:
    """
    Validate that the JSON structure matches the required format.
    Returns error message if invalid, None if valid.
    """
    try:
        # Check root level has subject_name
        if not isinstance(data, dict) or "subject_name" not in data:
            return "Missing 'subject_name' at root level"
        
        subject = data["subject_name"]
        if not isinstance(subject, dict):
            return "'subject_name' must be an object"
        
        # Check required fields in subject_name
        required_fields = ["title", "description", "chapters"]
        for field in required_fields:
            if field not in subject:
                return f"Missing required field '{field}' in subject_name"
        
        # Check chapters is an array
        if not isinstance(subject["chapters"], list):
            return "'chapters' must be an array"
        
        # Validate each chapter
        for i, chapter in enumerate(subject["chapters"]):
            if not isinstance(chapter, dict):
                return f"Chapter {i} must be an object"
            
            if "title" not in chapter:
                return f"Chapter {i} missing 'title'"
            
            if "topics" not in chapter:
                return f"Chapter {i} missing 'topics'"
            
            if not isinstance(chapter["topics"], list):
                return f"Chapter {i} 'topics' must be an array"
            
            # Validate each topic
            for j, topic in enumerate(chapter["topics"]):
                if not isinstance(topic, dict):
                    return f"Chapter {i}, Topic {j} must be an object"
                
                required_topic_fields = ["topic_id", "title", "content", "examples", 
                                       "real_world_applications", "keywords"]
                for field in required_topic_fields:
                    if field not in topic:
                        return f"Chapter {i}, Topic {j} missing '{field}'"
                
                # Validate arrays
                for array_field in ["examples", "real_world_applications", "keywords"]:
                    if not isinstance(topic[array_field], list):
                        return f"Chapter {i}, Topic {j} '{array_field}' must be an array"
        
        return None  # Valid structure
    except Exception as e:
        return f"Validation error: {str(e)}"


class JSONConverter:
    """Converts extracted text content to the required JSON format using OpenAI."""
    
    def __init__(self, openai_client: OpenAI):
        self.client = openai_client
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        Rough approximation: 1 token ≈ 4 characters for English text.
        This is a conservative estimate for truncation purposes.
        """
        return len(text) // 4
    
    def _truncate_to_token_limit(self, text: str, system_prompt: str, user_prompt_template: str, 
                                  filename: str, max_context_tokens: int, max_output_tokens: int) -> str:
        """
        Truncate text content to fit within token limits.
        
        Args:
            text: The text content to truncate
            system_prompt: The system prompt (will be counted)
            user_prompt_template: User prompt template with {filename} and {text_content} placeholders
            filename: The filename
            max_context_tokens: Maximum context tokens for the model (e.g., 128000)
            max_output_tokens: Maximum output tokens to reserve
            
        Returns:
            Truncated text that fits within token limits
        """
        # Estimate tokens for system prompt and user prompt wrapper
        system_tokens = self._estimate_tokens(system_prompt)
        user_wrapper = user_prompt_template.format(filename=filename, text_content="")
        user_wrapper_tokens = self._estimate_tokens(user_wrapper)
        
        # Reserve tokens: system + user wrapper + output + safety margin (5%)
        reserved_tokens = system_tokens + user_wrapper_tokens + max_output_tokens
        safety_margin = int(max_context_tokens * 0.05)  # 5% safety margin
        available_tokens = max_context_tokens - reserved_tokens - safety_margin
        
        # Estimate tokens for current text
        text_tokens = self._estimate_tokens(text)
        
        if text_tokens <= available_tokens:
            return text
        
        # Truncate to fit within available tokens
        # Convert tokens back to characters (approximate)
        max_chars = available_tokens * 4
        truncated = text[:max_chars]
        
        logger.warning(
            f"Text too long ({text_tokens} estimated tokens, limit: {available_tokens} tokens). "
            f"Truncating from {len(text)} to {len(truncated)} characters."
        )
        
        return truncated + "\n\n[Content truncated due to token limits. Consider processing in smaller chunks for very large documents.]"
    
    def convert_to_json(self, text_content: str, filename: str) -> Dict[str, Any]:
        """
        Convert extracted text to the required JSON format using OpenAI.
        
        Args:
            text_content: The extracted text from the file
            filename: Original filename for context
        
        Returns:
            Dictionary in the required JSON format
        """
        try:
            # Model context limits (gpt-4o-mini has 128000 token context window)
            MODEL_CONTEXT_LIMIT = 128000
            
            # Determine max_tokens based on content size (before truncation)
            content_length = len(text_content)
            if content_length > 300000:  # Very large documents (300K+ chars)
                max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "16000"))  # 16K tokens for large docs
            elif content_length > 100000:  # Medium-large documents
                max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "8000"))  # 8K tokens
            else:
                max_tokens = int(os.getenv("MAX_OUTPUT_TOKENS", "4000"))  # 4K tokens default
            
            # Create the prompt
            system_prompt = """You are an expert at analyzing educational content and structuring it into a well-organized format.
Your task is to analyze the provided content and convert it into a structured JSON format.

CRITICAL: You MUST follow this EXACT JSON structure. Do not add or remove any fields:

{
  "subject_name": {
    "title": "",
    "description": "",
    "chapters": [
      {
        "title": "",
        "topics": [
          {
            "topic_id": "",
            "title": "",
            "content": "",
            "examples": [],
            "real_world_applications": [],
            "keywords": []
          }
        ]
      }
    ]
  }
}

REQUIRED STRUCTURE:
- Root level: "subject_name" (object)
  - "title" (string): Subject title
  - "description" (string): Brief description of the subject
  - "chapters" (array): Array of chapter objects
    - Each chapter object:
      - "title" (string): Chapter title
      - "topics" (array): Array of topic objects
        - Each topic object:
          - "topic_id" (string): Unique identifier (e.g., "topic_1", "topic_2")
          - "title" (string): Topic title
          - "content" (string): Detailed content/explanation
          - "examples" (array): Array of example strings (can be empty [])
          - "real_world_applications" (array): Array of application strings (can be empty [])
          - "keywords" (array): Array of keyword strings (can be empty [])

Guidelines:
1. Identify the main subject from the content and use it as "subject_name" key
2. Break down the content into logical chapters
3. Within each chapter, identify distinct topics
4. For each topic, provide:
   - A unique topic_id (e.g., "topic_1", "topic_2", "topic_3")
   - Clear, descriptive title
   - Comprehensive content/explanation
   - Relevant examples: Extract concrete examples from the content. If the content mentions specific cases, instances, or illustrations, include them. For educational content, provide at least 2-3 examples when possible. If no examples are in the content, try to provide relevant educational examples that illustrate the concept.
   - Real-world applications: Identify practical applications, use cases, or real-world scenarios related to the topic. Think about how this concept is applied in practice, in society, or in professional contexts. Include at least 2-3 applications when possible.
   - Important keywords: Extract 5-10 key terms, concepts, or phrases that are central to understanding this topic
5. All arrays must be present. Strive to populate examples and real_world_applications with meaningful content rather than leaving them empty.
6. Ensure the structure is logical and educational
7. Return ONLY valid JSON matching this exact structure, no additional text or markdown formatting
8. The "subject_name" key should be the actual subject name from the content (e.g., "Mathematics", "Physics", "Chemistry", "Indian Polity")"""

            # User prompt template (will be filled after truncation)
            user_prompt_template = """Please analyze the following content and convert it to the required JSON format.

Filename: {filename}

Content:
{text_content}

Return the JSON structure as specified."""
            
            # Truncate text content to fit within token limits
            text_content = self._truncate_to_token_limit(
                text_content, 
                system_prompt, 
                user_prompt_template, 
                filename,
                MODEL_CONTEXT_LIMIT,
                max_tokens
            )
            
            # Create final user prompt with truncated content
            user_prompt = user_prompt_template.format(
                filename=filename,
                text_content=text_content
            )
            
            logger.info(f"Sending request to OpenAI API... (Content: {len(text_content)} chars, Max output tokens: {max_tokens})")
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using a cost-effective model, can be changed to gpt-4 for better results
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )
            
            # Extract JSON from response
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            try:
                json_output = json.loads(response_text)
                logger.info("Successfully parsed JSON response")
                
                # Validate the structure matches required format
                validation_error = validate_json_structure(json_output)
                if validation_error:
                    logger.warning(f"JSON structure validation warning: {validation_error}")
                    # Don't fail, but log the warning for debugging
                
                return json_output
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                logger.error(f"Response text: {response_text[:500]}")
                raise ValueError(f"Invalid JSON response from OpenAI: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error converting to JSON: {str(e)}", exc_info=True)
            raise

