# -*- coding: utf-8 -*-
#
# Author: Daniel J. Ramirez

def create_or_delete():
    user_id = request.args(0)
    group_id = request.args(1)
    store_id = request.args(2)

    if not user_id or not group_id or not store_id:
        raise HTTP(400)

    role = db((db.store_role.id_user == user_id)
            & (db.store_role.id_role == group_id)
            & (db.store_role.id_store == store_id)).select().first()

    print role

    action = 'created'
    if not role:
        db.store_role.insert(id_user=user_id, id_role=group_id, id_store=store_id)
    else:
        db(db.store_role.id == role.id).delete()
        action = 'deleted'

    return dict(status='ok', action=action)
