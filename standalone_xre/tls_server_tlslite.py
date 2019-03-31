from __future__ import print_function
from xre_common import *
import subprocess
try: import SocketServer
except ImportError: import socketserver as SocketServer
from tlslite.api import *
from tlslite.utils.dns_utils import is_valid_hostname
try: from tack.structures.Tack import Tack
except ImportError: pass
from tlslite.constants import CipherSuite, HashAlgorithm, SignatureAlgorithm, GroupName, SignatureScheme

"""
This is a pure python implementation of the XFiles Remote Explorer (XRE) server-side protocol.
The TLS channel is established using the tlslite-ng library (pure python, so any OS and both python 2 and 3 work)
By default this uses PyQT to show the HashView window for visual end-to-end verification,
if you want to disable it and not use PyQT, just provide the --nohv command line argument
"""


def printError(s):
    """Print error message and exit"""
    sys.stderr.write("ERROR: %s\n" % s)
    sys.exit(-1)


def printGoodConnection(connection, seconds, hv=None):
    print("  Handshake time: %.3f seconds" % seconds)
    print("  Version: %s" % connection.getVersionName())
    print("  Cipher: %s %s" % (connection.getCipherName(),
        connection.getCipherImplementation()))
    print("  Ciphersuite: {0}".\
            format(CipherSuite.ietfNames[connection.session.cipherSuite]))
    if connection.session.srpUsername:
        print("  Client SRP username: %s" % connection.session.srpUsername)
    if connection.session.clientCertChain:
        print("  Client X.509 SHA1 fingerprint: %s" %
            connection.session.clientCertChain.getFingerprint())
    else:
        print("  No client certificate provided by peer")
    if connection.session.serverCertChain:
        print("  Server X.509 SHA1 fingerprint: %s" %
            connection.session.serverCertChain.getFingerprint())
    if connection.version >= (3, 3) and connection.serverSigAlg is not None:
        scheme = SignatureScheme.toRepr(connection.serverSigAlg)
        if scheme is None:
            scheme = "{1}+{0}".format(
                HashAlgorithm.toStr(connection.serverSigAlg[0]),
                SignatureAlgorithm.toStr(connection.serverSigAlg[1]))
        print("  Key exchange signature: {0}".format(scheme))
    if connection.ecdhCurve is not None:
        print("  Group used for key exchange: {0}".format(\
                GroupName.toStr(connection.ecdhCurve)))
    if connection.dhGroupSize is not None:
        print("  DH group size: {0} bits".format(connection.dhGroupSize))
    if connection.session.serverName:
        print("  SNI: %s" % connection.session.serverName)
    if connection.session.tackExt:
        if connection.session.tackInHelloExt:
            emptyStr = "\n  (via TLS Extension)"
        else:
            emptyStr = "\n  (via TACK Certificate)"
        print("  TACK: %s" % emptyStr)
        print(str(connection.session.tackExt))
    if connection.session.appProto:
        print("  Application Layer Protocol negotiated: {0}".format(
            connection.session.appProto.decode('utf-8')))
    print("  Next-Protocol Negotiated: %s" % connection.next_proto)
    print("  Encrypt-then-MAC: {0}".format(connection.encryptThenMAC))
    print("  Extended Master Secret: {0}".format(connection.extendedMasterSecret))

    # PGP #
    from hashlib import sha256
    sha_ = sha256(connection.session.masterSecret)
    print("SHA256 of this session's master secret:\n",sha_.hexdigest())
    if hv is not None:
        hv.hvSignal.emit(bytearray(sha_.digest()))


def serverCmd(address,privateKey_, certChain_, hv=None):

    # key
    s = open(privateKey_, "r").read()
    # OpenSSL/m2crypto does not support RSASSA-PSS certificates
    privateKey = parsePEMKey(s, private=True, implementations=["python"])

    # cert
    s = open(certChain_, "r").read()
    x509 = X509()
    x509.parse(s)
    certChain = X509CertChain([x509])
        
    #############
    sessionCache = SessionCache()
    username = None
    sni = None
    if is_valid_hostname(address[0]):
        sni = address[0]

    class SimpleTCPRequestHandler(BaseRequestHandler):
        def handle(self):
            print("In request handler")
            rq = self.request.recv(100)
            print('Received request is: '+rq)
            print('Echoing...')
            self.request.sendall(rq+rq)
            print('Echoing completed')

    class XRERequestHandler(BaseRequestHandler):
        def handle(self):
            print("In XRE request handler")
            xre_server_session(self.request)


    class MyTLSServer(ThreadingMixIn, TLSSocketServerMixIn, SocketServer.TCPServer):
        # customize ciphersuites and crypto back-end
        # from tlslite import handshakesettings
        # handshakesettings.CIPHER_NAMES = ["aes128gcm"]
        # handshakesettings.CIPHER_IMPLEMENTATIONS = ["openssl","pycrypto"]

        def handshake(self, connection):
            print("About to handshake...")
            activationFlags = 0

            try:
                start = time.clock()
                settings = HandshakeSettings()
                settings.useExperimentalTackExtension=True
                settings.dhParams = None
                connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
                connection.handshakeServer(certChain=certChain,
                                           privateKey=privateKey,
                                           verifierDB=None,
                                           tacks=None,
                                           activationFlags=activationFlags,
                                           sessionCache=sessionCache,
                                           settings=settings,
                                           nextProtos=None,
                                           alpn=None,
                                           reqCert=False,
                                           sni=sni)
                stop = time.clock()
            except TLSRemoteAlert as a:
                if a.description == AlertDescription.user_canceled:
                    print(str(a))
                    return False
                else:
                    raise
            except TLSLocalAlert as a:
                if a.description == AlertDescription.unknown_psk_identity:
                    if username:
                        print("Unknown username")
                        return False
                    else:
                        raise
                elif a.description == AlertDescription.bad_record_mac:
                    if username:
                        print("Bad username or password")
                        return False
                    else:
                        raise
                elif a.description == AlertDescription.handshake_failure:
                    print("Unable to negotiate mutually acceptable parameters")
                    return False
                else:
                    raise
                
            connection.ignoreAbruptClose = True
            printGoodConnection(connection, stop-start, hv)
            return True

    # tlsd = MyTLSServer(address,SimpleTCPRequestHandler)
    tlsd = MyTLSServer(address,XRERequestHandler)
    tlsd.serve_forever()

def main_server_thread(hv=None):
    print("Listing network interfaces...")
    print(subprocess.check_output('ipconfig' if os.name == 'nt' else 'ifconfig', shell=True).decode('utf-8'))
    serverCmd(('0.0.0.0', 11111), 'dummykey.pem', 'dummycrt.pem', hv)


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--nohv':
        main_server_thread()
    else:
        from HashView import *
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        hv = HashView(None, 16, 3, 800, 800)
        t = threading.Thread(target=main_server_thread, args=(hv,))
        t.start()
        sys.exit(app.exec_())
