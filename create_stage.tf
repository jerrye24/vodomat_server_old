provider "google" {
    credentials = "${file("vodomat_key.json")}"
    project = "vodomat-257513"
    region = "us-east1"
}

resource "google_compute_firewall" "external_http" {
    name = "vodomat-external-http"
    network = "default"

    allow {
        protocol = "tcp"
        ports = ["80"]
    }

    source_tags = ["server"]
}

resource "google_compute_firewall" "external_mysql" {
    name = "vodomat-external-mysql"
    network = "default"

    allow {
        protocol = "tcp"
        ports = ["3306"]
    }

    source_tags = ["mysql"]
}

resource "google_compute_instance" "server" {
    name = "vodomat-server"
    machine_type = "n1-standard-1"
    zone = "us-east1-b"

    tags = ["server"]

    boot_disk {
        initialize_params {
            image = "ubuntu-os-cloud/ubuntu-1804-lts"
        }
    }

    network_interface {
        network = "default"
        access_config {}
    }

    metadata_startup_script = "sudo apt update; sudo apt install -y python-minimal"

    metadata = {
        ssh-keys = "jerrye:${file("vodomat.pub")}"
    }
}

resource "google_dns_managed_zone" "stage-zone" {
    name = "stage-zone"
    dns_name = "stage.vodomat.net."
}

resource "google_dns_record_set" "server" {
    name = "server.stage.vodomat.net."
    type = "A"
    ttl = 300
    managed_zone = "${google_dns_managed_zone.stage-zone.name}"
    rrdatas = ["${google_compute_instance.server.network_interface.0.access_config.0.nat_ip}"]
}

output "server_external_ip" {
    value = "${google_compute_instance.server.network_interface.0.access_config.0.nat_ip}"
}