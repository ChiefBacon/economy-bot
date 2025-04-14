# Economy Bot
A simple economy bot for discord

## Issues to be resolved/documented
- [ ] Low customizability
- [ ] Admin user is set in config file, not retreived from the database
- [x] No example config file
- [x] No Docker images published
- [ ] Web UI is incomplete and unstable
- [ ] The items for the shop are hardcoded, not retreived from the database
- [ ] No documentation
- [ ] Likely unstable
- [ ] No unit testing available

## Docker Images
Docker images are available. You can find an example of a `docker-compose.yml` file below
```yaml
services:
  economy-bot:
    image: ghcr.io/chiefbacon/simple-economy-bot:release
    restart: unless-stopped
    volumes:
      - ./config:/bot/config
  db:
    image: postgres
    restart: unless-stopped
    environment:
      POSTGRES_PASSWORD: <DATABASE PASSWORD HERE>
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```
Place your config file in the `./config` directory. There is also a `main` image available, which is even *less* stable than the release image.

## How to contribute
Make any changes you see fit, then make a pull request from your fork. I will review your changes and accept them if everything seems ok.

## Support
If you have any questions or comments, feel free to open a discussion or issue.

## License
This project is licensed under the [MIT license](LICENSE) and contains [third party packages](THIRD_PARTY.md).