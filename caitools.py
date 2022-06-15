import sys
import subprocess
from google.cloud import asset_v1
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
        elif "sc" in options and "sa" in options:
            await comparePermission(
                allArguments[allArguments.index("-sc") + 1],
                allArguments[allArguments.index("-sa") + 1],
            )
        else:
            comparePermissionHelpPage()
            exit()

    elif options[0] == "help":
        mainHelpPage()
    else:
        mainHelpPage()


async def initAuth():
    homePath = subprocess.run(['echo "$HOME"'], capture_output=True, text=True, shell=True, check=True)
    homePath = homePath.stdout.replace("\n", "")

    print("Sign in ......")
    subprocess.run(["gcloud auth application-default login"], capture_output=True, text=True, shell=True, check=True)
    subprocess.run(["gcloud auth login"], capture_output=True, text=True, shell=True, check=True)

    print("Exporting application key ...")
    subprocess.run([f"export GOOGLE_APPLICATION_CREDENTIALS={homePath}/application_default_credentials.json"],
                   capture_output=True, text=True, shell=True, check=True)


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
    policy.role.permissions:""
    """.format(i, r)
    if r is not None:
        query += "resource=//cloudresourcemanager.googleapis.com/{}".format(r)

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

    # Getting Response
    roles = []
    no = []
    lastCount = 0
    isEmpty = True
    async for item in result:
        isEmpty = False
        for c in range(0, len(item.policy.bindings)):
            if item.policy.bindings[c].role not in roles:
                if c == 0:
                    no.append(lastCount + 1)
                    lastCount += 1
                else:
                    lastCount += 1
                    no.append(lastCount)
                roles.append(item.policy.bindings[c].role)

        roles.sort()

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

    tb = PrettyTable()
    fieldNames = [
        f"{Fore.LIGHTBLUE_EX} No {Fore.RESET}",
        f"{Fore.LIGHTBLUE_EX} Role  {Fore.RESET}"
    ]
    tb.add_column(fieldNames[0], no)
    tb.add_column(fieldNames[1], roles, "l")

    print(f"""{tb}\n""")
    exit()


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

    projects = []
    assets = []
    resources = []
    isEmpty = True
    isProjectIncrement = False
    isAssetIncrement = False
    async for item in result:
        # print(item)
        isEmpty = False
        tmpAsset = ""

        if item.project not in projects:
            projects.append(item.project)
            isProjectIncrement = True
        else:
            isProjectIncrement = False

        if item.asset_type + "\n" not in assets:
            if isProjectIncrement:
                assets.append(f"{item.asset_type}\n")
                isAssetIncrement = True
            else:
                assets[-1] += f"{item.asset_type}\n"
                isAssetIncrement = False
        else:
            isAssetIncrement = False

        if item.resource + "\n" not in resources:
            if isAssetIncrement:
                resources.append(f"{item.resource}\n")
            else:
                resources[-1] += f"{item.resource}\n"

    # Formatting the output
    titleScope = Fore.RED + "Scope" + Fore.RESET
    titleIdentity = Fore.RED + "Identity" + Fore.RESET
    print("\n" + "=" * 100)
    print(f"""{titleScope}    : {s}\n{titleIdentity} : {i}""")
    print("=" * 100 + "\n")
    if isEmpty:
        print(f"\n\t {Fore.RED} No role for the spesific criteria is found {Fore.RESET}\n")
        exit()

    tb = PrettyTable()
    fieldNames = [
        f"{Fore.LIGHTBLUE_EX} Project {Fore.RESET}",
        f"{Fore.LIGHTBLUE_EX} Asset  {Fore.RESET}",
        f"{Fore.LIGHTBLUE_EX} Resource  {Fore.RESET}"
    ]
    tb.add_column(fieldNames[0], projects)
    tb.add_column(fieldNames[1], assets, "l")
    tb.add_column(fieldNames[2], resources, "l")

    print(f"""{tb}\n""")
    exit()


async def comparePermission(sc, sa):
    """
            Compare two Service Account role was have
            Options available :
                - -sc <scope>        : REQUIRED, scope can be a project, folder, or organization
                                       Options available : projects/{PROJECT_ID} , folders/{FOLDER_ID},
                                       or organizations/{ORGANIZATION_ID}
                                       Example : --compare-permission -sc projects/sample-project2212

                - -sa <SA1>,<SA2>,.. : REQUIRED, specify all Service Account will be compared. If more than one SA
                                       separate them with comma (,)
                                       Example : --compare-permission -sc projects/sample-project2212 -sa account1,account2

    """
    sas = sa.split(",")
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
        
        Usage               : caitools.py --see-permissioin -s [SCOPE] -i [IDENTITY] -r [RESOURCE]
        
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
                
                - -sc <scope>        : REQUIRED, scope can be a project, folder, or organization
                                       Example : projects/{PROJECT_ID} , folders/{FOLDER_ID}, or organizations/{ORGANIZATION_ID}
    
                - -sa <SA1>,<SA2>,.. : REQUIRED, specify all Service Account will be compared. If more than one SA
                                       separate them with comma (,)
                                       Example : -sa account1,account2
    
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
