# Football Match Predictor - Full Stack ML Application

A modern full-stack application built with Flask (Python backend) and React (JavaScript frontend) that uses machine learning to predict football match outcomes and identify top-performing players.

## Features

- **ML-Powered Predictions**: Uses Random Forest algorithm to predict match winners (Home/Away/Draw)
- **Player Analytics**: Identifies MVP candidates and top performers from both teams
- **Modern UI**: Responsive design with dark/light mode toggle
- **Real-time Predictions**: Interactive team selection and instant results
- **Data Visualization**: Progress bars and probability displays

## Tech Stack

### Backend
- **Flask**: Python web framework
- **scikit-learn**: Machine learning library
- **pandas**: Data manipulation
- **joblib**: Model persistence
- **CORS**: Cross-origin resource sharing

### Frontend
- **React**: JavaScript framework
- **Tailwind CSS**: Utility-first CSS framework
- **Vite**: Build tool and dev server

### Machine Learning
- **Random Forest Classifier**: For match outcome prediction
- **Feature Engineering**: Team and player performance metrics
- **Model Training**: API endpoint for retraining

## AWS Deployment Guide

### Prerequisites
1. AWS Account with appropriate permissions
2. AWS CLI installed and configured
3. Python 3.8+ and Node.js 16+ installed locally
4. Docker (optional, for containerized deployment)

### Option 1: AWS Elastic Beanstalk (Recommended)

#### Backend Deployment

1. **Prepare the Backend**:
   ```bash
   cd backend
   pip freeze > requirements.txt
   ```

2. **Create Elastic Beanstalk Application**:
   ```bash
   # Install EB CLI if not installed
   pip install awsebcli

   # Initialize EB application
   eb init football-predictor-backend --platform python-3.8 --region us-east-1

   # Create environment
   eb create football-predictor-prod --instance-type t3.small --single-instance
   ```

3. **Configure Environment Variables**:
   ```bash
   eb setenv FLASK_ENV=production
   eb setenv CORS_ORIGIN=https://your-frontend-domain.com
   ```

4. **Deploy**:
   ```bash
   eb deploy
   ```

#### Frontend Deployment

1. **Build the Frontend**:
   ```bash
   cd frontend
   npm run build
   ```

2. **Deploy to S3 + CloudFront**:
   ```bash
   # Create S3 bucket
   aws s3 mb s3://football-predictor-frontend

   # Upload build files
   aws s3 sync dist/ s3://football-predictor-frontend --delete

   # Create CloudFront distribution
   aws cloudfront create-distribution \
     --origin-domain-name football-predictor-frontend.s3.amazonaws.com \
     --default-root-object index.html
   ```

### Option 2: AWS ECS with Fargate (Containerized)

#### Backend Dockerfile
```dockerfile
FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:16-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
```

#### Deploy to ECS
```bash
# Build and push Docker images
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com

docker build -t football-predictor-backend ./backend
docker tag football-predictor-backend:latest your-account.dkr.ecr.us-east-1.amazonaws.com/football-predictor-backend:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/football-predictor-backend:latest

# Create ECS cluster and services
aws ecs create-cluster --cluster-name football-predictor
aws ecs create-service --cluster football-predictor --service-name backend --task-definition backend-task
```

### Option 3: AWS Lambda + API Gateway (Serverless)

#### Backend Lambda Function
```python
import json
from app import app

def lambda_handler(event, context):
    with app.test_client() as client:
        response = client.request(
            method=event['httpMethod'],
            path=event['path'],
            headers=event.get('headers', {}),
            data=event.get('body', '')
        )
        
        return {
            'statusCode': response.status_code,
            'headers': dict(response.headers),
            'body': response.data.decode('utf-8')
        }
```

#### Deploy with Serverless Framework
```bash
npm install -g serverless
serverless deploy
```

## ML Model Deployment Considerations

### Model Storage
- **S3**: Store trained models and datasets
- **Model Registry**: Use AWS SageMaker Model Registry for versioning

### Model Training
- **SageMaker**: For large-scale training jobs
- **EC2**: For custom training environments
- **Lambda**: For lightweight model updates

### Model Serving
- **SageMaker Endpoints**: Managed ML inference
- **EC2**: Custom inference servers
- **Lambda**: Serverless inference (limited by size)

## Environment Setup

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

# Frontend
cd frontend
npm install
npm run dev
```

### Production Environment Variables
```bash
# Backend
FLASK_ENV=production
CORS_ORIGIN=https://your-frontend-domain.com
MODEL_PATH=s3://your-bucket/models/
DATA_PATH=s3://your-bucket/data/

# Frontend
VITE_API_URL=https://your-backend-domain.com
```

## Data Management

### CSV Files Structure
- `games.csv`: Match data with features
- `leagues.csv`: League information
- `teams.csv`: Team details
- `players.csv`: Player statistics

### S3 Data Storage
```bash
# Upload data files
aws s3 cp data/ s3://your-bucket/data/ --recursive

# Set up data pipeline
aws glue create-job --name football-data-pipeline --script-location s3://your-bucket/scripts/
```

## Monitoring and Logging

### CloudWatch
- Application logs
- Performance metrics
- Error tracking

### X-Ray
- Request tracing
- Performance analysis

### CloudTrail
- API call logging
- Security monitoring

## Security Considerations

### IAM Roles
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/*"
    }
  ]
}
```

### VPC Configuration
- Private subnets for backend
- Public subnets for load balancers
- Security groups for access control

## Cost Optimization

### EC2 Instance Types
- **Development**: t3.micro ($8-10/month)
- **Production**: t3.small ($15-20/month)
- **ML Training**: c5.large ($70-80/month)

### S3 Storage Classes
- **Frequently accessed**: Standard
- **Infrequently accessed**: IA
- **Archival**: Glacier

## Scaling Considerations

### Auto Scaling
```bash
# Configure auto scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name football-predictor-asg \
  --min-size 1 \
  --max-size 10 \
  --desired-capacity 2
```

### Load Balancing
- Application Load Balancer
- Health checks
- SSL/TLS termination

## Backup and Recovery

### Database Backup
- Automated snapshots
- Cross-region replication

### Model Versioning
- SageMaker Model Registry
- S3 versioning
- Git LFS for model files

## Troubleshooting

### Common Issues
1. **CORS Errors**: Check CORS configuration
2. **Model Loading**: Verify S3 permissions
3. **Memory Issues**: Increase instance size
4. **Timeout Errors**: Optimize model inference

### Debug Commands
```bash
# Check application logs
eb logs

# SSH into instance
eb ssh

# Check S3 access
aws s3 ls s3://your-bucket/

# Test API endpoints
curl -X GET https://your-api-domain.com/api/health
```

## Performance Optimization

### Frontend
- Code splitting
- Image optimization
- CDN caching

### Backend
- Model caching
- Database connection pooling
- Async processing

### ML Model
- Model quantization
- Batch inference
- GPU acceleration

## Support and Maintenance

### Regular Tasks
- Security updates
- Model retraining
- Performance monitoring
- Cost optimization

### Documentation
- API documentation
- Deployment procedures
- Troubleshooting guides

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Contact

For questions or support, please open an issue on GitHub.



#   U p d a t e d   0 8 / 1 5 / 2 0 2 5   1 8 : 2 6 : 5 7  
 