mkdir -p apis data_zips
page=0
while [ $page -le 927 ] ; do
    # url="https://samate.nist.gov/SARD/api/test-cases/search?language%5B%5D=java&page=${page}&limit=100"
    url="https://samate.nist.gov/SARD/api/test-cases/search?language%5B%5D=c&page=${page}&limit=100"
    echo $url
    curl -o apis4c/api_$page.json $url
    page=$((page+1))
done
python download_datasets.py \
    --output_dir "data_zips"\
    --api_dir "apis4c"