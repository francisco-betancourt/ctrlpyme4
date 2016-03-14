# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez


@auth.requires_membership('Admin')
def create():
    """ args: [id_address] """
    address = db.address(request.args(0))
    if not address:
        redirect(URL('address', 'create', vars=dict(_next=URL('create'))))
    form = SQLFORM(db.store)
    form.vars.id_address = address.id
    if form.process().accepted:
        # insert store group
        db.auth_group.insert(role='Store %s' % form.vars.id)
        response.flash = T('form accepted')
        redirect(URL('index'))
    elif form.errors:
        response.flash = T('form has errors')
    return dict(form=form)


@auth.requires_membership('Admin')
def get():
    store = db.store(request.args(0))
    if not store:
        raise HTTP(404, T('Store NOT FOUND'))

    store_config = db(db.store_config.id_store == store.id).select()
    store_roles = db(db.store_role.id_store == store.id).select()
    return locals()


@auth.requires_membership('Admin')
def update():
    return common_update('store', request.args, _vars=request.vars)


@auth.requires_membership('Admin')
def delete():
    return common_delete('store', request.args)


@auth.requires_membership('Admin')
def index():
    def store_options(row):
        update_btn, hide_btn = supert_default_options(row)
        return update_btn, hide_btn, OPTION_BTN('vpn_key', URL('seals', args=row.id))
    title = T('stores')
    data = SUPERT(db.store, fields=[
        'name', {
            'fields': ['id_address.street', 'id_address.exterior'],
            'label_as': T('Address')
        }
    ], options_func=store_options)
    return locals()


def read_certificate(form):
    from cgi import FieldStorage
    #Check if you received both the certificate and private key
    print form.vars
    if form.vars.private_key=='' and form.vars.certificate=='':
        form.errors.certificate=T("Please input your certificate")
        form.errors.private_key=T("Please input your private key")
    if isinstance(form.vars.private_key,FieldStorage) and not isinstance(form.vars.certificate,FieldStorage):
        form.errors.certificate=T("Please input your certificate")
        form.errors.private_key=T("You must provide a private key and a certificate simultaneously")
        return
    if isinstance(form.vars.certificate,FieldStorage) and not isinstance(form.vars.private_key,FieldStorage):
        form.errors.certificate=T("You must provide a private key and a certificate simultaneously")
        form.errors.private_key=T("Please input your private key")
        return
    #If one is selected for deleting delete both
    if form.vars.certificate__delete=='on':
        form.vars.certificate_base64=None
        form.vars.no_certificado=None
        return
    if form.vars.private_key_delete=='on':
        form.vars.csdpass=None
    if isinstance(form.vars.certificate,str):
        return
    #Read certificate number
    cert_file=form.vars.certificate.file.read()
    form.vars.certificate.file.seek(0)
    from OpenSSL import crypto
    try:
        cert = crypto.load_certificate(crypto.FILETYPE_ASN1,cert_file)
        cert_pem=crypto.dump_certificate(crypto.FILETYPE_PEM,cert)
    except:
        form.errors.certificate=T("Invalid certificate file")
        return
    form.vars.certificate_number=hex(cert.get_serial_number())[2:-1].decode('hex')
    #Save certificate as base64
    from base64 import b64encode
    form.vars.certificate_base64=b64encode(cert_file)
    form.vars.certpem_base64=b64encode(cert_pem)

@auth.requires_membership('Admin')
def seals():
    store = db.store(request.args(0))
    if not store:
        raise HTTP(404,T('Store NOT FOUND'))
    db.store.id.readable=False
    form=SQLFORM(db.store,store,fields=['certificate','private_key'])
    print form[0],len(form[0])
    form[0].insert(2,DIV(
        LABEL(T('CSD password'),_class="control-label col-sm-3",_for="csdpass",_id="store_csdpass_label"),
        DIV(INPUT(_type="password", _name="csdpass",_id="store_csdpass",_class="form-control string"),_class="col-sm-9"),_class="form-group",_id="store_csdpass__row", _style="display:none;"))
    #On validation check for the certificate on accepted process the private key
    if form.process(onvalidation=read_certificate).accepted:
        #Now transform and store the user seals
        print "Ok"
    return locals()
