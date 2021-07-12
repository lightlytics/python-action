import pulumi_aws as aws

ca_config = aws.acmpca.CertificateAuthorityCertificateAuthorityConfigurationArgs(key_algorithm="RSA_4096",
                                                                                 signing_algorithm="SHA512WITHRSA",
                                                                                 subject=aws.acmpca.CertificateAuthorityCertificateAuthorityConfigurationSubjectArgs(
                                                                                     common_name="example.com", ), )
example = aws.acmpca.CertificateAuthority("example",
                                          certificate_authority_configuration=ca_config,
                                          permanent_deletion_time_in_days=7)
