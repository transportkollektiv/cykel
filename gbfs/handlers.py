from corsheaders.signals import check_request_enabled


# Allow CORS for All GBFS Urls
def cors_allow(sender, request, **kwargs):
    return request.path.startswith("/gbfs/")


check_request_enabled.connect(cors_allow)
