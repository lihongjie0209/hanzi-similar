#!/bin/bash
# Docker build and push script for hanzi-similar
# Automatically uses git tag for versioning

set -e

# Default values
PUSH=false
REGISTRY="lihongjie0209"
IMAGE_NAME="hanzi-similar"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
error() { echo -e "${RED}❌ $1${NC}"; }
warning() { echo -e "${YELLOW}⚠️ $1${NC}"; }

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --push)
            PUSH=true
            shift
            ;;
        --registry)
            REGISTRY="$2"
            shift 2
            ;;
        --image-name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--push] [--registry REGISTRY] [--image-name IMAGE_NAME]"
            echo "  --push              Push images to remote registry after building"
            echo "  --registry          Docker registry/username (default: lihongjie0209)"
            echo "  --image-name        Image name (default: hanzi-similar)"
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get current git tag
if CURRENT_TAG=$(git describe --tags --exact-match HEAD 2>/dev/null); then
    info "当前 HEAD 在 tag: $CURRENT_TAG"
elif LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null); then
    warning "当前 HEAD 不在任何 tag 上，使用最新 tag: $LATEST_TAG"
    CURRENT_TAG="$LATEST_TAG"
else
    error "没有找到任何 git tag，请先创建一个 tag"
    exit 1
fi

VERSION="$CURRENT_TAG"
FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME"

info "开始构建 Docker 镜像..."
info "版本: $VERSION"
info "镜像名称: $FULL_IMAGE_NAME"

# Build Docker image
info "构建 Docker 镜像..."
if docker build -t "$IMAGE_NAME" .; then
    success "Docker 镜像构建完成"
else
    error "Docker 构建失败"
    exit 1
fi

# Tag with version
info "添加版本标签: $VERSION"
if docker tag "$IMAGE_NAME" "${FULL_IMAGE_NAME}:$VERSION"; then
    success "版本标签添加完成"
else
    error "添加版本标签失败"
    exit 1
fi

# Tag with latest
info "添加 latest 标签"
if docker tag "$IMAGE_NAME" "${FULL_IMAGE_NAME}:latest"; then
    success "latest 标签添加完成"
else
    error "添加 latest 标签失败"
    exit 1
fi

success "镜像标签添加完成"
info "可用的镜像标签:"
docker images "$FULL_IMAGE_NAME"

if [ "$PUSH" = true ]; then
    info "推送镜像到远程仓库..."
    
    # Push version tag
    info "推送版本标签: $VERSION"
    if docker push "${FULL_IMAGE_NAME}:$VERSION"; then
        success "版本标签推送完成"
    else
        error "推送版本标签失败"
        exit 1
    fi
    
    # Push latest tag
    info "推送 latest 标签"
    if docker push "${FULL_IMAGE_NAME}:latest"; then
        success "latest 标签推送完成"
    else
        error "推送 latest 标签失败"
        exit 1
    fi
    
    success "所有镜像推送完成！"
    info "镜像地址:"
    echo -e "  - ${YELLOW}${FULL_IMAGE_NAME}:$VERSION${NC}"
    echo -e "  - ${YELLOW}${FULL_IMAGE_NAME}:latest${NC}"
else
    info "镜像构建完成，使用 --push 参数来推送到远程仓库"
    info "或者手动运行:"
    echo -e "  ${YELLOW}docker push ${FULL_IMAGE_NAME}:$VERSION${NC}"
    echo -e "  ${YELLOW}docker push ${FULL_IMAGE_NAME}:latest${NC}"
fi

success "脚本执行完成！"
