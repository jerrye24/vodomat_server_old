import models
from security import generate_password_hash, check_password_hash


async def validate_update_avtomat_form(conn, form):
    number = form.get('number')
    address = form.get('address')
    size = form.get('size')
    ph_number = form.get('ph_number')
    driver = form.get('driver')
    route = form.get('route')
    competitors = form.get('competitors')
    price = form.get('water_price')

    if not price:
        price = 0
    if not ph_number:
        ph_number = ''

    await models.update_avtomat(conn, number, address, size, ph_number, driver, route, competitors, price)


async def validate_create_user_form(conn, form):
    username = form.get('username')
    first_name = form.get('first_name')
    last_name = form.get('last_name')
    permission = form.get('permission')
    password = form.get('password')
    confirm_password = form.get('confirm_password')

    if not username:
        return 'username is required'
    if not password:
        return 'password is required'

    result = await conn.execute(models.users.select().where(models.users.c.username==username))
    copy_user = await result.first()
    if copy_user:
        return 'this username is already exists'
    
    if password != confirm_password:
        return 'the passwords are different'
    
    password_hash = generate_password_hash(password)
    await models.create_user(conn, username, first_name, last_name, password_hash, permission)


async def validate_update_user_form(conn, form):
    username = form.get('username')
    first_name = form.get('first_name')
    last_name = form.get('last_name')
    old_password = form.get('old_password')
    new_password = form.get('new_password')
    permission = form.get('permission')
    user_id = form.get('user_id')

    if not username:
        return 'username is required'
    if not permission:
        return 'permission is required'
    
    user = await models.get_user_by_id(conn, user_id)

    if old_password and new_password:
        if check_password_hash(old_password, user['password']):
            password = generate_password_hash(new_password)
        else:
            return 'invalid password'
    else:
        password = None
    
    await models.update_user(conn, user_id, username, first_name, last_name, permission, password)


async def validate_login_form(conn, form):
    username = form.get('username')
    password = form.get('password')

    if not username:
        return 'username is required'
    if not password:
        return 'password is required'
    
    user = await models.get_user_by_name(conn, username)

    if not user:
        return 'invalid username or password'
    if not check_password_hash(password, user['password']):
        return 'invalid username or password'
    else:
        return None
    
    return 'error'
