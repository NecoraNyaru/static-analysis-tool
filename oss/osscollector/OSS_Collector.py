"""
Dataset Collection Tool.
Author:		Seunghoon Woo (seunghoonwoo@korea.ac.kr)
Modified: 	December 16, 2020.
"""

import os
import subprocess
import re
import tlsh  # Please intall python-tlsh

"""GLOBALS"""

currentPath = os.getcwd()
gitCloneURLS = "sample"  # Please change to the correct file (the "sample" file contains only 10 git-clone urls)
clonePath = "repo_src/"  # Default path
tagDatePath = "repo_date/"  # Default path
resultPath = "repo_functions/"  # Default path
ctagsPath = (
    "/usr/local/bin/ctags"  # Ctags binary path (please specify your own ctags path)
)


# Generate TLSH
def computeTlsh(string):
    string = str.encode(string)
    hs = tlsh.forcehash(string)
    return hs


def removeComment(string):
    # Code for removing C/C++ style comments. (Imported from VUDDY and ReDeBug.)
    # ref: https://github.com/squizz617/vuddy
    c_regex = re.compile(
        r'(?P<comment>//.*?$|[{}]+)|(?P<multilinecomment>/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
        re.DOTALL | re.MULTILINE,
    )
    return "".join(
        [
            c.group("noncomment")
            for c in c_regex.finditer(string)
            if c.group("noncomment")
        ]
    )


def normalize(string):
    # Code for normalizing the input string.
    # LF and TAB literals, curly braces, and spaces are removed,
    # and all characters are lowercased.
    # ref: https://github.com/squizz617/vuddy
    return "".join(
        string.replace("\n", "")
        .replace("\r", "")
        .replace("\t", "")
        .replace("{", "")
        .replace("}", "")
        .split(" ")
    ).lower()


def hashing(repoPath):
    # This function is for hashing C/C++ functions
    # Only consider ".c", ".cc", and ".cpp" files
    possible = (".c", ".cc", ".cpp")

    fileCnt = 0
    funcCnt = 0
    lineCnt = 0

    resDict = {}

    for path, dir, files in os.walk(repoPath):
        for file in files:
            filePath = os.path.join(path, file)

            if file.endswith(possible):
                try:
                    # Execute Ctgas command
                    functionList = subprocess.check_output(
                        ctagsPath
                        + ' -f - --kinds-C=* --fields=neKSt "'
                        + filePath
                        + '"',
                        stderr=subprocess.STDOUT,
                        shell=True,
                    ).decode()

                    f = open(filePath, "r", encoding="UTF-8")

                    # For parsing functions
                    lines = f.readlines()
                    allFuncs = str(functionList).split("\n")
                    func = re.compile(r"(function)")
                    number = re.compile(r"(\d+)")
                    funcSearch = re.compile(r"{([\S\s]*)}")
                    tmpString = ""
                    funcBody = ""

                    fileCnt += 1

                    for i in allFuncs:
                        elemList = re.sub(r"[\t\s ]{2,}", "", i)
                        elemList = elemList.split("\t")
                        funcBody = ""

                        if (
                            i != ""
                            and len(elemList) >= 8
                            and func.fullmatch(elemList[3])
                        ):
                            funcStartLine = int(number.search(elemList[4]).group(0))
                            funcEndLine = int(number.search(elemList[7]).group(0))

                            tmpString = ""
                            tmpString = tmpString.join(
                                lines[funcStartLine - 1 : funcEndLine]
                            )

                            if funcSearch.search(tmpString):
                                funcBody = funcBody + funcSearch.search(
                                    tmpString
                                ).group(1)
                            else:
                                funcBody = " "

                            funcBody = removeComment(funcBody)
                            funcBody = normalize(funcBody)
                            funcHash = computeTlsh(funcBody)

                            if len(funcHash) == 72 and funcHash.startswith("T1"):
                                funcHash = funcHash[2:]
                            elif (
                                funcHash == "TNULL"
                                or funcHash == ""
                                or funcHash == "NULL"
                            ):
                                continue

                            storedPath = filePath.replace(repoPath, "")
                            if funcHash not in resDict:
                                resDict[funcHash] = []
                            resDict[funcHash].append(storedPath)

                            lineCnt += len(lines)
                            funcCnt += 1

                            print(
                                "[.] Hashing",
                                filePath,
                                ":",
                                funcHash,
                                "at",
                                funcStartLine,
                                "~",
                                funcEndLine,
                            )

                except subprocess.CalledProcessError as e:
                    print("Parser Error:", e)
                    continue
                except Exception as e:
                    print("Subprocess failed", e)
                    continue

    return resDict, fileCnt, funcCnt, lineCnt


def indexing(resDict, title, filePath):
    # For indexing each OSS

    fres = open(filePath, "w")
    fres.write(title + "\n")

    for hashval in resDict:
        if hashval == "" or hashval == " ":
            continue

        fres.write(hashval)

        for funcPath in resDict[hashval]:
            fres.write("\t" + funcPath)
        fres.write("\n")

    fres.close()


def main():
    with open(gitCloneURLS, "r", encoding="UTF-8") as fp:
        funcDateDict = {}
        lines = [l.strip("\n\r") for l in fp.readlines()]

        for eachUrl in lines:
            os.chdir(currentPath)
            repoName = (
                eachUrl.split("github.com/")[1].replace(".git", "").replace("/", "@@")
            )  # Replace '/' -> '@@' for convenience
            print("[+] Processing", repoName)

            try:
                cloneCommand = eachUrl + " " + clonePath + repoName
                cloneResult = subprocess.check_output(
                    cloneCommand, stderr=subprocess.STDOUT, shell=True
                ).decode()

                os.chdir(clonePath + repoName)

                dateCommand = 'git log --tags --simplify-by-decoration --pretty="format:%ai %d"'  # For storing tag dates
                dateResult = subprocess.check_output(
                    dateCommand, stderr=subprocess.STDOUT, shell=True
                ).decode()
                tagDateFile = open(tagDatePath + repoName, "w")
                tagDateFile.write(str(dateResult))
                tagDateFile.close()

                tagCommand = "git tag"
                tagResult = subprocess.check_output(
                    tagCommand, stderr=subprocess.STDOUT, shell=True
                ).decode()

                resDict = {}
                fileCnt = 0
                funcCnt = 0
                lineCnt = 0

                if tagResult == "":
                    # No tags, only master repo

                    resDict, fileCnt, funcCnt, lineCnt = hashing(clonePath + repoName)
                    if len(resDict) > 0:
                        if not os.path.isdir(resultPath + repoName):
                            os.mkdir(resultPath + repoName)
                        title = "\t".join(
                            [repoName, str(fileCnt), str(funcCnt), str(lineCnt)]
                        )
                        resultFilePath = (
                            resultPath + repoName + "/fuzzy_" + repoName + ".hidx"
                        )  # Default file name: "fuzzy_OSSname.hidx"

                        indexing(resDict, title, resultFilePath)

                else:
                    for tag in str(tagResult).split("\n"):
                        # Generate function hashes for each tag (version)

                        checkoutCommand = subprocess.check_output(
                            "git checkout -f " + tag,
                            stderr=subprocess.STDOUT,
                            shell=True,
                        )
                        resDict, fileCnt, funcCnt, lineCnt = hashing(
                            clonePath + repoName
                        )

                        if len(resDict) > 0:
                            if not os.path.isdir(resultPath + repoName):
                                os.mkdir(resultPath + repoName)
                            title = "\t".join(
                                [repoName, str(fileCnt), str(funcCnt), str(lineCnt)]
                            )
                            resultFilePath = (
                                resultPath + repoName + "/fuzzy_" + tag + ".hidx"
                            )

                            indexing(resDict, title, resultFilePath)

            except subprocess.CalledProcessError as e:
                print("Parser Error:", e)
                continue
            except Exception as e:
                print("Subprocess failed", e)
                continue


def collect(git_urls_path, output_dir, ctags_bin_path=None):
    """Callable entry point for the collector."""
    global gitCloneURLS, ctagsPath, currentPath, clonePath, tagDatePath, resultPath

    # Set the base path for all operations
    currentPath = output_dir

    # Configure paths based on the provided output_path
    gitCloneURLS = git_urls_path
    clonePath = os.path.join(currentPath, "repo_src/")
    tagDatePath = os.path.join(currentPath, "repo_date/")
    resultPath = os.path.join(currentPath, "repo_functions/")

    if ctags_bin_path:
        ctagsPath = ctags_bin_path

    # Ensure directories exist
    shouldMake = [clonePath, tagDatePath, resultPath]
    for eachRepo in shouldMake:
        if not os.path.isdir(eachRepo):
            os.mkdir(eachRepo)

    main()


""" EXECUTE """
if __name__ == "__main__":
    # When run directly, create directories in the script's location.
    shouldMake = [clonePath, tagDatePath, resultPath]
    for eachRepo in shouldMake:
        if not os.path.isdir(eachRepo):
            os.mkdir(eachRepo)
    main()
