#!/usr/bin/env bash
# Build + push both images to ECR (Path A). Run where Docker + AWS CLI are available.
#   AWS_REGION=ap-south-1 ./deploy/aws-deploy.sh
# After it finishes, create/point the two App Runner services at the pushed images
# (see DEPLOY.md). Brain first, then web with BRAIN_URL set to the brain's URL.
set -euo pipefail

AWS_REGION="${AWS_REGION:-ap-south-1}"
TAG="${TAG:-latest}"
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
ECR="${ACCOUNT}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "▶ Account ${ACCOUNT} · region ${AWS_REGION} · ECR ${ECR}"

for repo in pmguru-backend pmguru-frontend; do
  aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" >/dev/null 2>&1 \
    || aws ecr create-repository --repository-name "$repo" --region "$AWS_REGION" >/dev/null
done

aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR"

echo "▶ Building backend"
docker build -t "${ECR}/pmguru-backend:${TAG}" "${ROOT}/backend"
docker push "${ECR}/pmguru-backend:${TAG}"

echo "▶ Building frontend"
docker build -t "${ECR}/pmguru-frontend:${TAG}" "${ROOT}/frontend"
docker push "${ECR}/pmguru-frontend:${TAG}"

cat <<NEXT

✅ Images pushed:
   ${ECR}/pmguru-backend:${TAG}
   ${ECR}/pmguru-frontend:${TAG}

Next (see DEPLOY.md):
  1) Create App Runner 'pmguru-brain' from pmguru-backend  (port 8000, health /health,
     env GROQ_API_KEY + DATABASE_URL).
  2) Create App Runner 'pmguru-web' from pmguru-frontend    (port 3000, env BRAIN_URL=<brain url>).
NEXT
