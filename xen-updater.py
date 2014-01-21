import urllib, os, logging, re

from xml.dom.minidom import parse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

logger.info('')
logger.info('*****************************************')
logger.info(' Created by : SteeveGL.DEV')
logger.info(' Contact : steevegl.dev@gmail.com')
logger.info('*****************************************')
logger.info('')
logger.info('Script started.')

xmlurl = 'http://updates.xensource.com/XenServer/updates.xml'

xml = urllib.urlopen(xmlurl)
dom = parse(xml)

serverversions = dom.getElementsByTagName("serverversions")
patches = dom.getElementsByTagName("patches")

reboot = False

xs_version = os.popen("cat /etc/redhat-release | awk -F ' ' '{ print $3 }' | awk -F '-' '{ print $1 }'").read()
hostid = os.popen('xe host-list --minimal').read()

logger.info('Citrix XenServer version found is ' + str(xs_version))

def Patched(uuid):
    patch_list = os.popen("xe patch-list").read()
    try:
        patch_list = re.findall(uuid, patch_list)[0]
        #logger.info('Already updated')
        return True
    except:
        #logger.info(uuid)
        return False

for versions in serverversions:

    for version in versions.getElementsByTagName("version"):

        Loc_Ver = re.split('\.', xs_version.rstrip('\n'))
        #logger.info(str(Loc_Ver))
        New_Ver = re.split('\.', version.attributes['value'].value.rstrip('\n'))
        #logger.info(str(New_Ver))
        if Loc_Ver[0] == New_Ver[0] and Loc_Ver[1] <= New_Ver[1]:

            logger.info('')
            logger.info('*****************************************')
            logger.info(version.attributes['name'].value)
            logger.info('Version: ' + version.attributes['value'].value + ' Build: ' + version.attributes['build-number'].value)
            logger.info('Latest: ' + version.attributes['latest'].value)
            logger.info('URL: ' + version.attributes['url'].value)
            logger.info('*****************************************')
            logger.info('Patches:')

            for ver_patch in version.getElementsByTagName("patch"):
                uuid = ver_patch.attributes['uuid'].value

                found = False

                if not Patched(uuid):

                    found = True
                    for P_patch in patches:

                        for patch in P_patch.getElementsByTagName("patch"):

                            if patch.attributes['uuid'].value == uuid:
                                logger.info('  Name: ' + patch.attributes['name-label'].value)
                                logger.info('  Release date: ' + patch.attributes['timestamp'].value)
                                logger.info('  Description: ' + patch.attributes['name-description'].value)
                                if patch.attributes['after-apply-guidance'].value == 'restartHost':
                                    logger.info('  Need reboot')
                                    reboot = True
                                if patch.attributes['after-apply-guidance'].value == 'restartXAPI':
                                    logger.info('  Need restart XAPI')
                                    reboot = True
                                logger.info('  Patch URL: ' + patch.attributes['patch-url'].value)
                                logger.info('  URL: ' + patch.attributes['url'].value)
                                logger.info('')
                                if patch.attributes['patch-url'].value <> "":
                                    logger.info('  Downloading...')
                                    os.system('mkdir temp && cd temp/ && wget ' + patch.attributes['patch-url'].value)
                                    logger.info('  Decompressing...')
                                    os.system('unzip temp/*.zip -d temp')
                                    os.system('rm temp/*.zip')
                                    logger.info('  Upload patch...')
                                    os.system('xe patch-upload file-name=temp/' + patch.attributes['name-label'].value + '.xsupdate')
                                    logger.info('  Applying patch...')
                                    os.system('xe patch-apply uuid=' + patch.attributes['uuid'].value + ' host-uuid=' + hostid )
                                    logger.info('  Done.')
                                    os.system('rm -R -f temp')

                                else:
                                    logger.info('  No patch url, skipped...')
                                logger.info('')
                                logger.info('')

            if not found:
                logger.info('  Up-to-date.')
