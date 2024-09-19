from glob import glob
import os
import pkg_resources

from tutor import hooks as tutor_hooks

from .__about__ import __version__

config = {
    "defaults": {
        "VERSION": __version__,
        "DOCKER_IMAGE": "{{ DOCKER_REGISTRY }}overhangio/openedx-mfe-skilredi:{{ MFE_VERSION }}",
        "HOST": "{{ SKILREDI_MFE_HOST }}",
        "COMMON_VERSION": "{{ OPENEDX_COMMON_VERSION }}",
        "CADDY_DOCKER_IMAGE": "{{ DOCKER_IMAGE_CADDY }}",
        # S3 MFE Staticfiles
        # ----------------------
        # The bucket name to use for S3 static files
        "STATIC_FILES_BUCKET_NAME": "SET_ME_PLEASE",
        # AWS S3 settings
        "AWS_STATIC_FILES_ACCESS_KEY_ID": "SET_ME_PLEASE",
        "AWS_STATIC_FILES_SECRET_KEY": "SET_ME_PLEASE",
        "DEPLOY_S3": False,
        "ACCOUNT_MFE_APP_SKILREDI": {
            "name": "account",
            "repository": "https://github.com/edx/frontend-app-account",
            "port": 1997,
            "env": {
                "production": {
                    "COACHING_ENABLED": "",
                    "ENABLE_DEMOGRAPHICS_COLLECTION": "",
                },
            },
        },
        "GRADEBOOK_MFE_APP_SKILREDI": {
            "name": "gradebook",
            "repository": "https://github.com/edx/frontend-app-gradebook",
            "port": 1994,
        },
        "LEARNING_MFE_APP_SKILREDI": {
            "name": "learning",
            "repository": "https://github.com/edx/frontend-app-learning",
            "port": 2000,
        },
        "PROFILE_MFE_APP_SKILREDI": {
            "name": "profile",
            "repository": "https://github.com/edx/frontend-app-profile",
            "port": 1995,
             "env": {
                "production": {
                    "ENABLE_LEARNER_RECORD_MFE": "true",
                },
            },
        },
    },
}

# tutor_hooks.Filters.COMMANDS_INIT.add_item(
#     (
#         "lms",
#         ("mfe-skilredi", "tasks", "lms", "init"),
#     )
# )
tutor_hooks.Filters.IMAGES_BUILD.add_item(
    (
        "mfe-skilredi",
        ("plugins", "mfe-skilredi", "build", "mfe"),
        "{{ MFE_DOCKER_IMAGE_SKILREDI }}",
        (),
    )
)


@tutor_hooks.Filters.COMPOSE_MOUNTS.add()
def _mount_frontend_apps(volumes, name):
    """
    If the user mounts any repo named frontend-app-APPNAME, then make sure
    it's available in the APPNAME service container. This is only applicable
    in dev mode, because in production, all MFEs are built and hosted on the
    singular 'mfe' service container.
    """
    prefix = "frontend-app-"
    if name.startswith(prefix):
        # Assumption:
        # For each repo named frontend-app-APPNAME, there is an associated
        # docker-compose service named APPNAME. If this assumption is broken,
        # then Tutor will try to mount the repo in a service that doesn't exist.
        app_name = name.split(prefix)[1]
        volumes += [(app_name, "/openedx/app")]
    return volumes


@tutor_hooks.Filters.IMAGES_PULL.add()
@tutor_hooks.Filters.IMAGES_PUSH.add()
def _add_remote_mfe_image_iff_customized(images, user_config):
    """
    Register MFE image for pushing & pulling if and only if it has
    been set to something other than the default.

    This is work-around to an upstream issue with MFE config. Briefly:
    User config is baked into MFE builds, so Tutor cannot host a generic
    pre-built MFE image. Howevever, individual Tutor users may want/need to
    build and host their own MFE image. So, as a compromise, we tell Tutor
    to push/pull the MFE image if the user has customized it to anything
    other than the default image URL.
    """
    image_tag = user_config["MFE_DOCKER_IMAGE"]
    if not image_tag.startswith("docker.io/overhangio/openedx-mfe:"):
        # Image has been customized. Add to list for pulling/pushing.
        images.append(("mfe-skilredi", image_tag))
    return images

####### Boilerplate code
# Add the "templates" folder as a template root
tutor_hooks.Filters.ENV_TEMPLATE_ROOTS.add_item(
    pkg_resources.resource_filename("tutormfe_skilredi", "templates")
)
# Render the "build" and "apps" folders
tutor_hooks.Filters.ENV_TEMPLATE_TARGETS.add_items(
    [
        ("mfe-skilredi/build", "plugins"),
        ("mfe-skilredi/apps", "plugins"),
    ],
)
# Load patches from files
for path in glob(
    os.path.join(
        pkg_resources.resource_filename("tutormfe_skilredi", "patches"),
        "*",
    )
):
    with open(path, encoding="utf-8") as patch_file:
        tutor_hooks.Filters.ENV_PATCHES.add_item((os.path.basename(path), patch_file.read()))

# Add configuration entries
tutor_hooks.Filters.CONFIG_DEFAULTS.add_items(
    [(f"MFE_{key}_SKILREDI", value) for key, value in config.get("defaults", {}).items()]
)
tutor_hooks.Filters.CONFIG_UNIQUE.add_items(
    [(f"MFE_{key}_SKILREDI", value) for key, value in config.get("unique", {}).items()]
)
tutor_hooks.Filters.CONFIG_OVERRIDES.add_items(list(config.get("overrides", {}).items()))
