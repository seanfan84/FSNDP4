# FSNDP4 Full Stack Nano Degree Project 4 : Catalog App

This project is a catalog app, which people can view catalog and products but only logged in user can create new product.
the creater of a product will be able to delete and modify the product.

administrator would have full access to every product,
and extra previlage to create/edit/delete categories.


## Prerequisites
* Install VirtialBox and Vagrant

* Use a command line console which supports SSH (Linux commandline or git bash)

## Getting Started
* clone the repository to your local machine
* in command line window, navigate to the repository
* Change directory to the directory which has Vagrantfile in it, and run
```
vagrant up
```
* If vagrant is up successfully, run
```
vagrant ssh
```
* After you login with ssh, change directory by typing:
```
cd /vagrant/fsndp4
```

### Running on localhost
if you are running localhost on port 5000
your starting page will be:

* [http://localhost:5000/](http://localhost:5000/)

## Viewing as Admin
The database has been pre configured to have an admin user.
At this stage admin is hard coded into the backend, the full permission is give to the user with email
```
admin@catalogapp.com
```
and the password is 
```
11111111
```
If you plan to start fresh, you need to sign up with this email address immediately.

### Permission
As admin, you will have
```
New Category button in the sidebar
New Product in a categoy (admin only)
Edit Category in a category (admin only)
Delete Category in Edit Category, it will delete all products under it. (admin only)
Admin also has the permission to control all product even if it is created by others

```


## Viewing as a guest

If you do not log in, you will be viewing as a guest which has view permission only.

You will be redirected to home page from where you can access login page

## Login/Sign Up

Remember me feature is not provided.

3rd Party login with Google and Facebook is supplied.

The 3rd party login will try to fetch your email address, username.

If your facebook is registered with a mobile number which means the app could not get an email,

the login will fail.

## Logged in User

Here is the operation a logged in user can have.
### Logout
It clears cookie, and session
### Add new product

### Edit the product created by the user.

### Delete the product created by the user.


## Author

* **Sean Fan** - *Initial work* - [SeanFan84](https://github.com/seanfan84)

## License

This project is not licensed.

## Acknowledgments

* Hat tip to anyone who's code was used
* Inspiration
* etc
