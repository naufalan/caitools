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

    elif options[0] == "HELP":
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
                no.append(lastCount+1)
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


async def lagiTesting():
    # Create client
    client = asset_v1.AssetServiceAsyncClient()

    # Initialize request
    scope = "projects/infra-sandbox-291106"
    query = """
        policy:"user:naufal.nafis@cermati.com"
        policy.role.permissions:""
        resource:infra-sandbox-291106
        """

    # //cloudresourcemanager.googleapis.com/projects/infra-sandbox-291106 => Scope satu project

    request = asset_v1.SearchAllIamPoliciesRequest
    request.scope = scope
    request.query = query
    result = await client.search_all_iam_policies(
        request={
            "scope": scope,
            "query": query
        }
    )

    print("=" * 100)
    async for item in result:
        print(item)
        print("=" * 100)


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
