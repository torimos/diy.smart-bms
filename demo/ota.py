import urequests
import fsutils as fs

def ota_update(ota_path = "", tag_file_name = "/tag"):

    def get_latest_release_info(repo_owner = "torimos", repo_name = "diy.smart-bms", token=None):
        """
        Get the latest release information from a GitHub repository.

        :param repo_owner: Owner of the repository.
        :param repo_name: Name of the repository.
        :param token: GitHub personal access token (optional).
        :return: Latest release information as a dictionary.
        """
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        #print(url)
        headers = {
            'User-Agent': 'SMART-BMS-ESP32'
        }
        if token:
            headers['Authorization'] = f'token {token}'
        
        response = urequests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        return None

    def find_asset_by_name(release_info, asset_name):
        """
        Find an asset in the release info by its name.

        :param release_info: Release information dictionary.
        :param asset_name: Name of the asset to find.
        :return: Asset download URL or None if not found.
        """
        assets = release_info.get('assets', [])
        for asset in assets:
            if asset['name'] == asset_name:
                return asset['browser_download_url']
        return None

    def get_installed_version(version_file):
        if fs.exists(version_file):
            with open(version_file, "r") as file:
                version = file.read().strip()
            return version
        return None
    
    def update_installed_version(version_file, tag):
        with open(version_file, "w") as file:
            file.write(tag)

    cur_tag = get_installed_version(tag_file_name)
    print("Installed Tag Name:", cur_tag, "Checking for newer version...")
    release_info = get_latest_release_info()
    if release_info != None:
        release_id = release_info['id']
        tag_name = release_info['tag_name']
        release_ota_file_url = find_asset_by_name(release_info, "release.tar.gz")

        if tag_name != cur_tag:
            print("Newer version found:", tag_name, "Starting OTA update...")
            print("Release ID:", release_id)
            print("Downloading OTA File:", release_ota_file_url)
            #fs.delete_directory(ota_path)
            r = urequests.get(release_ota_file_url)
            if r.status_code == 200:
                fs.decompress(r.content, ota_path)
            r.close()
            r = None
            update_installed_version(tag_file_name, tag_name)
            print("OTA update is done!")
            print("Updated to version:", get_installed_version(tag_file_name))
            import machine
            machine.soft_reset()
        else:
            print("Latest version already deployed.")
    else:
        print("No releases found!")
    