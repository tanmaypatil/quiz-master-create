import json
import boto3
from datetime import datetime
import uuid
import logging
import base64
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('quiz')


def lambda_handler(event, context):
    try:
        # Get credentials from environment variables
        expected_username = os.environ.get('BASIC_AUTH_USERNAME')
        expected_password = os.environ.get('BASIC_AUTH_PASSWORD')

        # Check if environment variables are set
        if not expected_username or not expected_password:
            logger.error('Basic auth credentials not configured')
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Server configuration error'})
            }

        # Get Authorization header (check both cases)
        headers = event.get('headers', {})
        auth_header = headers.get(
            'Authorization') or headers.get('authorization')

        if not auth_header or not auth_header.startswith('Basic '):
            return {
                'statusCode': 401,
                'headers': {
                    'WWW-Authenticate': 'Basic realm="Restricted Area"'
                },
                'body': json.dumps({'error': 'Authentication required'})
            }

        try:
            # Extract and decode the base64 credentials
            base64_credentials = auth_header.split(' ')[1]
            credentials = base64.b64decode(base64_credentials).decode('utf-8')
            username, password = credentials.split(
                ':', 1)  # Split only on first colon

            # Validate credentials
            if username != expected_username or password != expected_password:
                return {
                    'statusCode': 401,
                    'headers': {
                        'WWW-Authenticate': 'Basic realm="Restricted Area"'
                    },
                    'body': json.dumps({'error': 'Invalid credentials'})
                }
        except (ValueError, UnicodeDecodeError) as e:
            logger.error(f'Error processing authentication: {str(e)}')
            return {
                'statusCode': 401,
                'headers': {
                    'WWW-Authenticate': 'Basic realm="Restricted Area"'
                },
                'body': json.dumps({'error': 'Invalid authentication format'})
            }
        except Exception as e:
            logger.error(f'Unexpected error: {str(e)}')
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'Internal server error'})
            }
            # Authentication successful - proceed with your main logic
        logger.info(f'Authentication successful for user: {username}')

        # Parse the incoming event
        body = json.loads(event['body']) if 'body' in event else event
        # check the quiz_data
        logger.info(f'quiz data : {body.get("quiz_data")}')

        # Generate unique ID if not provided
        quiz_id = body.get('id', str(uuid.uuid4()))
        logger.info(f'quiz id : {quiz_id}')

        # Prepare the item to insert
        item = {
            'quiz_name': body['quiz_name'],
            'id': quiz_id,
            'prompt': body['prompt'],
            'quiz_data': body['quiz_data'],
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }

        # Insert item into DynamoDB
        response = table.put_item(Item=item)
        logger.info(f'response from put : {response}')

        # Return success response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Quiz inserted successfully',
                'quiz_id': quiz_id,
                'quiz_name': body['quiz_name']
            })
        }

    except KeyError as e:
        # Handle missing required fields
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Missing required field: {str(e)}'
            })
        }

    except Exception as e:
        # Handle other errors
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }


# Example usage payload:
"""
{
    "quiz_name": "tech quiz - india 2025",
    "prompt": "Generate a quiz about recent tech developments in India",
    "quiz_data": [
        {
            "question": "Which Indian initiative was launched in 2025 to accelerate quantum computing research?",
            "options": [
                "National Mission on Quantum Technologies (NM-QT) Phase II",
                "Digital India Quantum Initiative",
                "Quantum Computing Excellence Program",
                "India Quantum Research Consortium"
            ],
            "correct": 0
        }
    ]
}
"""
