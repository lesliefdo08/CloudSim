"""
API Router Registration
Centralized router management for all API versions
"""

from fastapi import APIRouter

from app.config import settings


# Main API router
api_router = APIRouter()


def register_v1_routes(router: APIRouter) -> None:
    """
    Register all v1 API routes
    Import and include routers from api/v1/
    """
    # Import auth router
    from app.api.v1.auth import router as auth_router
    
    # Import IAM routers
    from app.api.v1.iam_users import router as iam_users_router
    from app.api.v1.iam_groups import router as iam_groups_router
    from app.api.v1.iam_policies import router as iam_policies_router
    from app.api.v1.iam_access_keys import router as iam_access_keys_router
    
    # Import VPC routers
    from app.api.v1.vpcs import router as vpcs_router
    from app.api.v1.subnets import router as subnets_router
    from app.api.v1.security_groups import router as security_groups_router
    
    # Import EC2 routers
    from app.api.v1.instances import router as instances_router
    from app.api.v1.images import router as images_router
    from app.api.v1.volumes import router as volumes_router
    
    # Import S3 router
    from app.api.v1.s3 import router as s3_router
    
    # Import S3 Advanced router
    from app.api.v1.s3_advanced import router as s3_advanced_router
    
    # Import CloudWatch router
    from app.api.v1.cloudwatch import router as cloudwatch_router
    
    # Import CloudWatch Logs and Alarms routers
    from app.api.v1.cloudwatch_logs import router as cloudwatch_logs_router
    from app.api.v1.cloudwatch_alarms import router as cloudwatch_alarms_router
    
    # Import RDS router
    from app.api.v1.rds import router as rds_router
    
    # Import Lambda router
    from app.api.v1.lambda_api import router as lambda_router
    
    # Import CloudFormation router
    from app.api.v1.cloudformation import router as cloudformation_router
    
    # Import example router
    from app.api.v1.examples import router as examples_router
    
    # Register auth routes
    router.include_router(auth_router)
    
    # Register IAM routes
    router.include_router(iam_users_router, prefix="/iam")
    router.include_router(iam_groups_router, prefix="/iam")
    router.include_router(iam_policies_router, prefix="/iam")
    router.include_router(iam_access_keys_router, prefix="/iam")
    
    # Register VPC routes
    router.include_router(vpcs_router)
    router.include_router(subnets_router)
    router.include_router(security_groups_router)
    
    # Register EC2 routes
    router.include_router(instances_router)
    router.include_router(images_router)
    router.include_router(volumes_router)
    
    # Register S3 routes
    router.include_router(s3_router)
    router.include_router(s3_advanced_router)
    
    # Register CloudWatch routes
    router.include_router(cloudwatch_router)
    router.include_router(cloudwatch_logs_router)
    router.include_router(cloudwatch_alarms_router)
    
    # Register RDS routes
    router.include_router(rds_router)
    
    # Register Lambda routes
    router.include_router(lambda_router)
    
    # Register CloudFormation routes
    router.include_router(cloudformation_router)
    
    # Register example routes
    router.include_router(examples_router)
    
    # TODO: Import and register service routers
    # Example structure:
    #
    # from app.api.v1 import instances, vpcs, volumes
    #
    # router.include_router(
    #     instances.router,
    #     prefix="/instances",
    #     tags=["EC2 Instances"]
    # )
    #
    # router.include_router(
    #     vpcs.router,
    #     prefix="/vpcs",
    #     tags=["VPC"]
    # )
    #
    # router.include_router(
    #     volumes.router,
    #     prefix="/volumes",
    #     tags=["EBS Volumes"]
    # )


def setup_routers(app) -> None:
    """
    Setup all API routers on FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    # Create v1 router
    v1_router = APIRouter()
    register_v1_routes(v1_router)
    
    # Include v1 router with prefix
    api_router.include_router(
        v1_router,
        prefix=settings.API_V1_PREFIX
    )
    
    # Include main API router in app
    app.include_router(api_router)
