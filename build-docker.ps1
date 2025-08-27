param([switch]$Push)
$tag = git describe --tags --exact-match HEAD 2>$null
if (-not $tag) { $tag = git describe --tags --abbrev=0 2>$null }
Write-Host "Building image with tag: $tag"
docker build -t hanzi-similar .
docker tag hanzi-similar "lihongjie0209/hanzi-similar:$tag"
docker tag hanzi-similar "lihongjie0209/hanzi-similar:latest"
if ($Push) { 
    docker push "lihongjie0209/hanzi-similar:$tag"
    docker push "lihongjie0209/hanzi-similar:latest"
}
