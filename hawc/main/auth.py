from mozilla_django_oidc.auth import OIDCAuthenticationBackend
import jwt
import time


class LoginGovAuthenticationBackend(OIDCAuthenticationBackend):
    def generate_jwt(self):

        private_key_fp = self.get_settings("RSA_KEY_FP")
        with open(private_key_fp, "r") as file:
            private_key = file.read()

        exp = int(time.time()) + (60 * 60 * 5)  # five hours from now
        payload = {
            "iss": self.OIDC_RP_CLIENT_ID,
            "sub": self.OIDC_RP_CLIENT_ID,
            "aud": self.OIDC_OP_TOKEN_ENDPOINT,
            "jti": "garbage",
            "exp": exp,
        }
        return jwt.encode(payload, private_key, algorithm="RS256")

    def get_token(self, payload):
        payload["client_assertion_type"] = "urn:ietf:params:oauth:client-assertion-type:jwt-bearer"
        payload["client_assertion"] = self.generate_jwt()
        return super().get_token(payload)
