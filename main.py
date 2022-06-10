import sys
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

    if options[0] == "see-permission":
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

    elif options[0] == "help":
        mainHelpPage()
    else:
        mainHelpPage()


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
        print(ex.args[0])
        exit()

    # Getting Response
    roles = []
    no = []
    lastCount = 0
    isEmpty = True
    async for item in result:
        isEmpty = False
        for c in range(0, len(item.policy.bindings)):
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
    print("\n")
    if isEmpty:
        print(f"\t {Fore.RED} No role for the spesific criteria is found {Fore.RESET}\n")
        exit()

    tb = PrettyTable(vertical_char="\t|", junction_char="\t+")
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
        print(ex.args[0])
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
    print("\n")
    print("=" * 100)
    print(f"""
        {titleScope}    : {s}
        {titleIdentity} : {i}
    """)
    print("=" * 100)
    print("\n")
    if isEmpty:
        print(f"\t {Fore.RED} No role for the spesific criteria is found {Fore.RESET}\n")
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


async def comparePermission(s1, s2, sc, r=None):
    """
            Compare two Service Account role was have
            Options available :
                - -sc <scope>        : REQUIRED, scope can be a project, folder, or organization
                                       Options available : projects/{PROJECT_ID} , folders/{FOLDER_ID},
                                       or organizations/{ORGANIZATION_ID}
                                       Example : --compare-permission -sc projects/sample-project2212

                - -s1 <SA>           : REQUIRED, specify first Service Account
                                       Example : --compare-permission -sc projects/sample-project2212 -s1 serviceAccount:{SA}

                - -s2 <SA>          : REQUIRED, specify second Service Account
                                      Example : --compare-permission -sc projects/sample-project2212 -s1 serviceAccount:{SA} -s2 serviceAccount:{SA}

    """


async def test():
    # Create a client
    client = asset_v1.AssetServiceAsyncClient()

    # Initialize request arguments
    scope = "projects/{}".format("infra-sandbox-291106")
    analysis_query = asset_v1.IamPolicyAnalysisQuery()
    analysis_query.scope = scope
    analysis_query.resource_selector.full_resource_name = f"//cloudresourcemanager.googleapis.com/{scope}"
    # analysis_query.IdentitySelector.identity = "user:naufal.nafis@cermati.com"
    analysis_query.Options.output_group_edges = True
    analysis_query.Options.output_resource_edges = True
    request = asset_v1.AnalyzeIamPolicyRequest(analysis_query=analysis_query)

    # Make the request
    response = await client.analyze_iam_policy(request=request)

    # Show the response
    print("Type data : {}\n\n".format(type(response.main_analysis.analysis_results)))
    print(response.main_analysis.analysis_results)


def mainHelpPage():
    print(
        """
        Descriptions    : Simple python tools to automate several routine task including see identity permission,
                          compare two identity permission & get all resource which have public access
        
        Usage           : caitools.py [MENU] [OPTIONS] [OPTIONS2] ...
        
        Available Menu  : --see-permission
                          --compare-permission
                          --get-public-resource
                          * to see available options in each menu see : caitools.py [MENU] --help
        """
    )


def seePermissionHelpPage():
    print(
        """
            See the permission which identity has, the identity can be a user or SA
            Options available :
                - -i <identity>     : REQUIRED, specify the identity (can be user or SA)
                                      Example : if user => user:{email} or if SA => serviceAccount:{SA}
                
                - -s <scope>        : REQUIRED, scope can be a project, folder, or organization
                                      Options available : projects/{PROJECT_ID} , folders/{FOLDER_ID},
                                      or organizations/{ORGANIZATION_ID}
                
                - -r <resource>     : Specify the resource which permission is set to the identity, it will search
                                      all the IAM policies with in the specified scope if not specified.
                                      Options available : projects/{PROJECT_ID} , folders/{FOLDER_ID}, or organizations/{ORGANIZATION_ID}.
            """
    )


def getPublicHelpPage():
    print(
        """
            See which resource have an public access
            Options available :
                - -i <identity>     : REQUIRED, specify the member type
                                      Options available : allUser & allAuthUser

                - -s <scope>        : REQUIRED, scope can be a project, folder, or organization
                                      Options available : projects/{PROJECT_ID} , folders/{FOLDER_ID},
                                      or organizations/{ORGANIZATION_ID}
            """
    )


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # Buat Testing2
    # asyncio.run(lagiTesting())
    # exit()

    if len(sys.argv) == 1:
        mainHelpPage()
        exit()

    global allArguments
    allArguments = sys.argv
    opts = [opt.lstrip("--" or "-") for opt in sys.argv[1:] if opt.startswith("-") or opt.startswith("--")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-") and not arg.startswith("--")]
    # print("OPTIONS : {}".format(opts))
    # print("ARGS : {}".format(args))
    asyncio.run(main(opts, args))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
