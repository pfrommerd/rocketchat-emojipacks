#!/usr/bin/env python3
import argparse
import getpass
from rocketchat_API.rocketchat import RocketChat
import requests
import validators
import os
import yaml

def reduce_kwargs(kwargs):
    if 'kwargs' in kwargs:
        for arg in kwargs['kwargs'].keys():
            kwargs[arg] = kwargs['kwargs'][arg]

        del kwargs['kwargs']
    return kwargs

def get_file_or_url(resource):
    if validators.url(resource):
        return requests.get(resource).content
    elif os.path.isfile(resource):
        with open(resource, 'rb') as f:
            return f.read()
    else:
        raise IOError("Could not get: {}".format(resource))


def do_post(rocket_chat, method, files=None, use_json=True, **kwargs):
        reduced_args = reduce_kwargs(kwargs)
        # Since pass is a reserved word in Python it has to be injected on the request dict
        # Some methods use pass (users.register) and others password (users.create)
        if 'password' in reduced_args and method != 'users.create':
            reduced_args['pass'] = reduced_args['password']
        if use_json:
            return rocket_chat.req.post(rocket_chat.server_url + rocket_chat.API_path + method,
                                         json=reduced_args,
                                         files=files,
                                         headers=rocket_chat.headers,
                                         verify=rocket_chat.ssl_verify,
                                         proxies=rocket_chat.proxies,
                                         timeout=rocket_chat.timeout
                                       )
        else:
            return rocket_chat.req.post(rocket_chat.server_url + rocket_chat.API_path + method,
                                     data=reduced_args,
                                     files=files,
                                     headers=rocket_chat.headers,
                                     verify=rocket_chat.ssl_verify,
                                     proxies=rocket_chat.proxies,
                                     timeout=rocket_chat.timeout
                                 )


def create_emoji(client, name, aliases, image_data):
    files = {"emoji": image_data}
    ret = do_post(client, "emoji-custom.create", files=files, name=name, aliases=','.join(aliases), use_json=False)
    if not ret.ok and not "already in use" in ret.text:
        raise IOError(ret.json()["error"])
    return ret.ok

def do_create_all(client, emojis):
    for emoji in emojis:
        name = emoji["name"]
        aliases = emoji["aliases"] if "aliases" in emoji else []
        try:
            src = get_file_or_url(emoji["src"])
        except IOError as e:
            print("Failed to get emoji {} source: {}".format(name, emoji["src"]))
            continue

        aliases_list = ','.join(aliases)
        print("Creating emoji {}{}...".format(name, " with aliases: {}".format(aliases_list) if aliases else ""), end="")

        try:
            success = create_emoji(rocket, name, aliases, src)
            print("success" if success else "already exists")
        except IOError as e:
            print("fail")
            print("Error creating emoji: {}".format(e))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, type=str)
    parser.add_argument("--user", default="", type=str)
    parser.add_argument("--password", default="", type=str)
    parser.add_argument("--pass_file", default="", type=str)
    parser.add_argument("--emojipack", default="", type=str)

    args = parser.parse_args()

    username = input("Username: ") if not args.user else args.user
    if args.pass_file:
        with open(args.pass_file) as f:
            password = f.read().strip()
    else:
        password = getpass.getpass("Password: ") if not args.password else args.password


    print("Logging in...")
    rocket = RocketChat(username, password, server_url=args.server)

    authenticated_user = rocket.me().json()
    print("Authenticated as '{}'".format(authenticated_user["name"]))

    if args.emojipack:
        try:
            emojis = yaml.safe_load(get_file_or_url(args.emojipack))["emojis"]
        except:
            print("Could not load emoji pack: {}".format(args.emojipack))
            return
        do_create_all(emojis)

if __name__=="__main__":
    main()
