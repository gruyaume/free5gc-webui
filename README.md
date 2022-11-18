# free5gc-webui-operator

[free5GC](https://www.free5gc.org/) is an open source 5G Core network implementation. This charmed
operator allows for automated deployment and lifecycle operations.

## Usage

```bash
juju deploy free5gc-webui-operator --trust --channel=edge
```

## Relations

### Mongo DB

```bash
juju deploy mongodb-k8s
juju relate free5gc-webui mongodb-k8s
```

## Image

- **[free5gc-webui](https://github.com/gruyaume/free5gc-webui-rock)**: ghcr.io/gruyaume/free5gc-webui:1.1.1
