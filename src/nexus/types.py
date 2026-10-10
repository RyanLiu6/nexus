from typing import TypedDict


class R2Credentials(TypedDict):
    """Cloudflare R2 storage credentials for S3-compatible storage.

    Retrieved from Terraform outputs during deployment and passed to PyInfra
    as extra-vars for configuring Foundry's S3 storage backend.

    Attributes:
        endpoint: R2 endpoint URL for the storage bucket.
        access_key: R2 access key ID for authentication.
        secret_key: R2 secret access key for authentication.
        bucket: Name of the R2 storage bucket.
    """

    endpoint: str
    access_key: str
    secret_key: str
    bucket: str
