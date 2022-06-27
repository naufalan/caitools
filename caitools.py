import sys
import subprocess
import json
from os import path
from google.cloud import asset_v1
# from google.cloud import resourcemanager_v3
import asyncio
from prettytable_custom import *
from colorama import init
from colorama import Fore


async def main(options=[], arguments=[]):
    # Main function to redirect based on argument
    """
    :param options: Contain all command options for navigate through menu
    :param arguments: Contain any mandatory data for some menu

    Available Menu :
        - see-permission     : See all permission for specific user or SA
        - compare-permission : Compare two user or SA permission
        - get-public-resource : Get which resource that have public access
    """
    options = [i.lower() for i in options]

    if options[0] == 'init-auth':
        await initAuth()
        exit()
    elif options[0] == "see-permission":
        # Options -i & -s are required
        if len(arguments) < 2:
            seePermissionHelpPage()
            exit()
        elif "i" in options and "s" in options:
            if "r" in options:
                await seePermission(
                    allArguments[allArguments.index("-i") + 1],
                    allArguments[allArguments.index("-s") + 1],
                    allArguments[allArguments.index("-r") + 1],
                )
            else:
                await seePermission(
                    allArguments[allArguments.index("-i") + 1],
                    allArguments[allArguments.index("-s") + 1],
                )
        else:
            seePermissionHelpPage()
            exit()

    elif options[0] == 'get-public-resource':
        # All options are required == 2
        if len(arguments) != 2:
            getPublicHelpPage()
            exit()
        elif "i" in options and "s" in options:
            await seePublicResource(
                allArguments[allArguments.index("-i") + 1],
                allArguments[allArguments.index("-s") + 1]
            )
        else:
            getPublicHelpPage()
            exit()

    elif options[0] == 'compare-permission':
        # All options are required == 2
        if len(arguments) != 2:
            comparePermissionHelpPage()
            exit()
        elif "s" in options and "i" in options:
            await comparePermission(
                allArguments[allArguments.index("-s") + 1],
                allArguments[allArguments.index("-i") + 1],
            )
        else:
            comparePermissionHelpPage()
            exit()

    elif options[0] == "help":
        mainHelpPage()
    else:
        mainHelpPage()


async def initAuth():
    print("\nInitialize Application Authentication\n" + "=" * 100)
    isSaIsExist = False
    keyPath = input("\nEnter the absolute path of SA key: ")

    # Checking SA is exist
    isSaIsExist = path.exists(keyPath)
    while not isSaIsExist:
        print("SA key not found")
        keyPath = input("Enter the absolute path of SA key: ")
        isSaIsExist = path.exists(keyPath)

    homePath = subprocess.run(['echo "$HOME"'], capture_output=True, text=True, shell=True, check=True)
    homePath = homePath.stdout.replace("\n", "")

    # Checking gcloud config directory is exist
    isGcloudConfDirectoryExist = False
    isGcloudConfDirectoryExist = path.isdir(f"{homePath}/.config/gcloud")
    if not isGcloudConfDirectoryExist:
        print(f"Gcloud config directory not found on {homePath}/.config/gcloud")
        exit()

    cp = subprocess.run([f"cp {keyPath} {homePath}/.config/gcloud/application_default_credentials.json"],
                        capture_output=True, text=True, shell=True, check=True)
    cp = cp.stdout

    subprocess.run([f"export GOOGLE_APPLICATION_CREDENTIALS={homePath}/.config/gcloud/application_default_credentials"
                    f".json"],
                   capture_output=True, text=True, shell=True, check=True)

    print("Done\n")


async def seePermission(i, s, r=None):
    """
    See the permission which identity has, the identity can be a user or SA
    Options available :
        - -i <identity>     : REQUIRED, specify the identity (can be user or SA)
                              Example : if user => user:{email} or if SA => serviceAccount:{SA}\n

        - -s <scope>        : REQUIRED, scope can be a project, folder, or organization
                              Options available : projects/{PROJECT_ID} , folders/{FOLDER_ID},
                              or organizations/{ORGANIZATION_ID}\n

        - -r <resource>  : Specify the resource which permission is set to the identity, it will search
                           all the IAM policies with in the specified scope if not specified.
                           Options available : {PROJECT_ID} , {FOLDER_ID}, or {ORGANIZATION_ID}.
    """

    # Create client
    client = asset_v1.AssetServiceAsyncClient()

    # Initialize request
    scope = s
    query = """
    policy:"{}"
    """.format(i, r)
    if r is not None:
        query += "resource=//cloudresourcemanager.googleapis.com/{}".format(r)

    query = query.replace("\n", "")
    request = asset_v1.SearchAllIamPoliciesRequest
    request.scope = scope
    request.query = query
    request.order_by = "assetType DESC"

    # Send the request
    try:
        result = await client.search_all_iam_policies(
            request={
                "scope": scope,
                "query": query
            }
        )
    except Exception as ex:
        if ex.grpc_status_code.name == 'PERMISSION_DENIED':
            print("\n Current user doesn't have permission to performing this search policies")
        elif ex.grpc_status_code.name == 'UNAVAILABLE':
            print("\n Can't connect to Google APIs, please check current network connection")
        exit()

    # Compose initial JSON output
    jeson = {"query": {}}
    jeson["query"]["type"] = "see-permission"
    jeson["query"]["scope"] = s
    jeson["query"]["identity"] = [i]

    if r is not None:
        jeson["query"]["resource"] = r

    arrResults = []

    # Getting Response
    no = []
    lastCount = 0
    isEmpty = True
    async for item in result:
        isEmpty = False

        o = {"asset-type": item.asset_type, "project": item.project}
        roles = []

        for c in range(0, len(item.policy.bindings)):
            if item.policy.bindings[c].role not in roles:
                roles.append(item.policy.bindings[c].role)
        roles.sort()
        o["role"] = roles
        o["resource"] = item.resource
        arrResults.append(o)

    jeson["result"] = arrResults

    # Formatting the output
    titleScope = Fore.RED + "Scope" + Fore.RESET
    titleIdentity = Fore.RED + "Identity" + Fore.RESET
    titleResource = Fore.RED + "Resource" + Fore.RESET
    print("\n")
    print("=" * 100)
    print(f"""
{titleScope}    : {s}
{titleIdentity} : {i}
{titleResource} : {r}
    """)
    print("=" * 100)
    if isEmpty:
        print(f"\n\t {Fore.RED} No role for the spesific criteria is found {Fore.RESET}\n")
        exit()

    jesonDump = json.dumps(jeson, indent=4)
    print("\n" + jesonDump)

    exit()


async def testing():
    # Create client
    client = resourcemanager_v3.ProjectsAsyncClient()

    # Compose the request
    request = resourcemanager_v3.SearchProjectsRequest()
    # request.query = "projects/infra-sandbox-291106"

    # Send the request
    results = await client.search_projects(request=request)

    async for item in results:
        print(item)


async def seePublicResource(i, s):
    """
        See the permission which identity has, the identity can be a user or SA
        Options available :
            - -i <identity>     : REQUIRED, specify the member type
                                  Options available : allUser & allAuthUser

            - -s <scope>        : REQUIRED, scope can be a project, folder, or organization
                                  Options available : projects/{PROJECT_ID} , folders/{FOLDER_ID},
                                  or organizations/{ORGANIZATION_ID}\n
    """

    # Create client
    client = asset_v1.AssetServiceAsyncClient()

    # Initialize request
    if i.lower() == "alluser":
        i = "allUsers"
    elif i.lower() == "allauthuser":
        i = "allAuthenticatedUsers"

    scope = s
    query = """
        memberTypes:"{}"
        """.format(i)

    query = query.replace("\n", "")
    request = asset_v1.SearchAllIamPoliciesRequest
    request.scope = scope
    request.query = query

    # Send the request
    try:
        result = await client.search_all_iam_policies(
            request={
                "scope": scope,
                "query": query
            }
        )
    except Exception as ex:
        if ex.grpc_status_code.name == 'PERMISSION_DENIED':
            print("\n Current user doesn't have permission to performing this search policies")
        elif ex.grpc_status_code.name == 'UNAVAILABLE':
            print("\n Can't connect to Google APIs, please check current network connection")
        exit()

    # Compose initial JSON output
    jeson = {"query": {}}
    jeson["query"]["type"] = "see-permission"
    jeson["query"]["scope"] = s
    jeson["query"]["identity"] = [i]
    jeson["result"] = []

    projects = []
    assets = []
    results = []
    resources = []
    isEmpty = True
    isProjectIncrement = False
    isAssetIncrement = False

    # Composing JSON result output
    arrResult = []
    o = {"project": "", "assets": []}
    arrAssets = []
    jAsset = {}
    arrResources = []
    jResource = {}

    async for item in result:
        isEmpty = False
        tmpAsset = ""

        jAsset = {}
        jResource = {}
        o = {}

        if item.project not in projects:
            projects.append(item.project)

            o["project"] = item.project
            o["assets"] = []
            arrResult.append(o)
            isProjectIncrement = True

        else:
            isProjectIncrement = False

        # Search project object by its project name value
        objProject = list(filter(lambda i: i['project'] == item.project, arrResult))
        objProject = objProject[0]
        objProjectPos = arrResult.index(next((filter(lambda i: i['project'] == item.project, arrResult))))

        if item.asset_type + "\n" not in assets:
            if isProjectIncrement:
                assets.append(f"{item.asset_type}\n")

                jAsset["asset-type"] = item.asset_type
                jAsset["resources"] = []
                objProject["assets"].append(jAsset)

                isAssetIncrement = True
            else:
                assets[-1] += f"{item.asset_type}\n"

                jAsset["asset-type"] = item.asset_type
                jAsset["resources"] = []
                objProject["assets"].append(jAsset)

                isAssetIncrement = True

        elif isProjectIncrement:
            jAsset["asset-type"] = item.asset_type
            jAsset["resources"] = []
            objProject["assets"].append(jAsset)
            isAssetIncrement = True

        else:
            isAssetIncrement = False

        # Get project assets array
        arrAssets = objProject["assets"]
        objAsset = list(filter(lambda i: i['asset-type'] == item.asset_type, arrAssets))
        objAsset = objAsset[0]
        objAssetPos = objProject["assets"].index(next((filter(lambda i: i['asset-type'] == item.asset_type, arrAssets))))

        if item.resource + "\n" not in resources:
            if isAssetIncrement:
                resources.append(f"{item.resource}\n")

                jResource["resource"] = item.resource
                jResource["role"] = item.policy.bindings[0].role
                objAsset["resources"].append(jResource)

            else:
                resources[-1] += f"{item.resource}\n"

                jResource["resource"] = item.resource
                jResource["role"] = item.policy.bindings[0].role
                objAsset["resources"].append(jResource)

        objProject["assets"][objAssetPos] = objAsset
        arrResult[objProjectPos] = objProject

    jeson["result"] = arrResult
    jesonDump = json.dumps(jeson, indent=4)

    # Formatting the output
    titleScope = Fore.RED + "Scope" + Fore.RESET
    titleIdentity = Fore.RED + "Identity" + Fore.RESET
    print("\n" + "=" * 100)
    print(f"""\n{titleScope}    : {s}\n{titleIdentity} : {i}\n""")
    print("=" * 100 + "\n")
    if isEmpty:
        print(f"\n\t {Fore.RED} No role for the spesific criteria is found {Fore.RESET}\n")
        exit()

    print(f"""{jesonDump}\n""")
    exit()


async def comparePermission(sc, sa):
    """
        Description       : Compare two or more Service Account role

        Usage             : caitools.py --compare-permission -sc [SCOPE] -sa [SA1,SA2,..]

        Options available :

                - -s <scope>     : REQUIRED, scope can be a project, folder, or organization
                                   Example : projects/{PROJECT_ID} , folders/{FOLDER_ID}, or organizations/{ORGANIZATION_ID}

                - -i <SA1>,<SA2> : REQUIRED, specify two Service Account that will be compared, separate them with comma (,)
                                   Example : -i account1,account2

    """
    sas = sa.split(",")
    if len(sas) != 2:
        comparePermissionHelpPage()
        exit()

    tb = PrettyTable()

    # Total result, example if all 3 SA have role binding, this variable should have an 3 as value
    countResult = 0
    roleResults = []
    isEmpty = True

    for serviceAcc in sas:
        # Create client
        try:
            client = asset_v1.AssetServiceAsyncClient()
        except Exception as ex:
            print(ex)
            print(f"\nPlease run command {Fore.RED} caitools.py --init-auth {Fore.RESET}")
            exit()

        # Initialize request
        scope = sc
        query = """
            policy:"serviceAccount:{}"
            policy.role.permissions:""
        """.format(serviceAcc)

        query = query.replace("\n", "")
        request = asset_v1.SearchAllIamPoliciesRequest
        request.scope = scope
        request.query = query

        # Send the request
        result = None
        try:
            result = await client.search_all_iam_policies(
                request={
                    "scope": scope,
                    "query": query
                }
            )
        except Exception as ex:
            if ex.grpc_status_code.name == 'PERMISSION_DENIED':
                print("\n Current user doesn't have permission to performing this search policies")
            elif ex.grpc_status_code.name == 'UNAVAILABLE':
                print("\n Can't connect to Google APIs, please check current network connection")
            exit()

        roleResult = [""]
        async for item in result:
            isEmpty = False
            for i in range(0, len(item.policy.bindings)):
                if item.policy.bindings[i].role not in roleResult[-1]:
                    if len(roleResults) == 0:
                        roleResult[-1] += item.policy.bindings[i].role + "\n"

                    else:
                        if item.policy.bindings[i].role not in roleResults[-1]:
                            roleResult[-1] += Fore.RED + item.policy.bindings[i].role + Fore.RESET + "\n"

                        elif item.policy.bindings[i].role in roleResults[-1]:
                            roleResult[-1] += item.policy.bindings[i].role + "\n"

        roleResults.append(roleResult[-1])
        tb.add_column(f"{Fore.LIGHTBLUE_EX} {serviceAcc} {Fore.RESET}", roleResult, 'l')
        roleResult = []

    # Formatting the output
    titleScope = Fore.RED + "Scope" + Fore.RESET
    titleIdentity = Fore.RED + "Service Account" + Fore.RESET
    print("\n" + "=" * 100)
    print(f"""
{titleScope}\t\t: {sc}
{titleIdentity}\t: {sa}
    """)
    print("=" * 100 + "\n")

    if isEmpty:
        print(f"\n\t {Fore.RED} No role for the specific criteria is found {Fore.RESET}\n")
        exit()

    print(tb)
    print("")


def mainHelpPage():
    print(
        """
        Descriptions    : Simple python tools to automate several routine task including see identity permission,
                          compare two identity permission & get all resource which have public access
        
        Usage           : caitools.py [MENU] [OPTIONS] [OPTIONS2] ...
        
        Available Menu  : --init-auth => Initialize application credentials
                          --see-permission
                          --compare-permission
                          --get-public-resource
                          * to see available options in each menu see : caitools.py [MENU] --help
        """
    )


def seePermissionHelpPage():
    print(
        """
        Descriptions        : See the role which identity has, the identity can be a user or SA
        
        Usage               : caitools.py --compare-permissioin -s [SCOPE] -i [IDENTITY] -r [RESOURCE]
        
        Options available   :
        
                - -s <scope>        : REQUIRED, scope can be a project, folder, or organization
                                      Example : projects/{PROJECT_ID} , folders/{FOLDER_ID}, or organizations/{ORGANIZATION_ID}
                
                - -i <identity>     : REQUIRED, specify the identity (can be user or SA)
                                      Example : if user => user:{email} or if SA => serviceAccount:{SA}
                
                - -r <resource>     : Specify the resource which permission is set to the identity, it will search
                                      all the IAM policies with in the specified scope if resource is not specified.
                                      Example : projects/{PROJECT_ID} , folders/{FOLDER_ID}, or organizations/{ORGANIZATION_ID}.
        """
    )


def getPublicHelpPage():
    print(
        """
        Description         : See which resource have an public access (allUser / allAuthenticatedUser)
        
        Usage               : --get-public-resource -s [SCOPE] -i [IDENTITY]
        
        Options available   :
                
                - -s <scope>        : REQUIRED, scope can be a project, folder, or organization
                                      Example : projects/{PROJECT_ID} , folders/{FOLDER_ID}, or organizations/{ORGANIZATION_ID}
                
                - -i <identity>     : REQUIRED, specify the user type
                                      Example : allUser & allAuthUser
        """
    )


def comparePermissionHelpPage():
    print(
        """
        Description       : Compare two or more Service Account role
            
        Usage             : caitools.py --compare-permission -sc [SCOPE] -sa [SA1,SA2,..]
            
        Options available :
                
                - -s <scope>     : REQUIRED, scope can be a project, folder, or organization
                                   Example : projects/{PROJECT_ID} , folders/{FOLDER_ID}, or organizations/{ORGANIZATION_ID}
    
                - -i <SA1>,<SA2> : REQUIRED, specify two Service Account that will be compared, separate them with comma (,)
                                   Example : -i account1,account2
    
         """
    )


if __name__ == '__main__':

    if len(sys.argv) == 1:
        mainHelpPage()
        exit()

    global allArguments
    allArguments = sys.argv
    opts = [opt.lstrip("--" or "-") for opt in sys.argv[1:] if opt.startswith("-") or opt.startswith("--")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-") and not arg.startswith("--")]
    asyncio.run(main(opts, args))
