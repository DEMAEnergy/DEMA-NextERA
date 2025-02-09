package sa.com.demaenergy.mining.manager;

import akka.actor.typed.ActorRef;
import akka.actor.typed.Behavior;
import akka.actor.typed.javadsl.*;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import sa.com.demaenergy.mining.manager.MinersController.Message.MinersIps;

import java.io.IOException;
import java.net.*;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.http.HttpResponse.BodyHandlers;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.CompletableFuture;

public class PrepareMiners extends AbstractBehavior<PrepareMiners.Message> {
    private final ActorRef<MinersController.Message> minersController;
    private final List<Miner> miners = new ArrayList<>();
    private final ActorRef<Message> self;
    private int numberOfServersToCheck = -1;
    private final Logger log;

    public PrepareMiners(ActorContext<Message> context, ActorRef<MinersController.Message> minersController, Duration timeout, TimerScheduler<Message> timers) {
        super(context);
        this.minersController = minersController;
        this.log = context.getLog();
        context.setReceiveTimeout(timeout, Message.ReceiveTimeout.INSTANCE);
        this.self = context.getSelf();
    }

    public static Behavior<PrepareMiners.Message> create(ActorRef<MinersController.Message> minersController, Duration timeout) {
        return Behaviors.withTimers(
                timers -> Behaviors.setup(
                        context -> new PrepareMiners(context, minersController, timeout, timers)
                )
        );
    }

    @Override
    public Receive<Message> createReceive() {
        return newReceiveBuilder()
                .onMessage(Message.ScanFromSubnet.class, this::onScanFromSubnet)
                .onMessage(Message.ServerReplied.class, this::onMinerReplied)
                .onMessage(Message.GetMacAddress.class, this::onGetMacAddress)
                .onMessage(Message.CheckScanFinished.class, this::onCheckScanFinished)
                .onMessageEquals(Message.ReceiveTimeout.INSTANCE, this::onReceiveTimeout)
                .build();
    }

    private Behavior<Message> onReceiveTimeout() {
        log.info("Receive timeout");
        log.info(STR."Miners left to check \{numberOfServersToCheck}");
        if (numberOfServersToCheck == 0) {
            minersController.tell(new MinersIps(miners.stream()
                    .map(miner -> new MinersController.Miner(miner.id, miner.ipAddress, 80))
                    .toList())
            );
            return Behaviors.stopped();
        }
        minersController.tell(
                new MinersController.ScanFailed()
        );
        return Behaviors.stopped();
    }

    private Behavior<Message> onGetMacAddress(Message.GetMacAddress getMacAddress) {

        log.debug(STR."Getting mac address for \{getMacAddress.miner.ipAddress}");
        try (HttpClient httpClient = HttpClient.newHttpClient()) {
            ObjectMapper objectMapper = new ObjectMapper();
            HttpRequest build = HttpRequest.newBuilder().GET()
                    .uri(URI.create(STR."http:/\{getMacAddress.miner.ipAddress}:80/api/v1/info")) //todo: make sure this works for all types of miners
                    .build();

            httpClient.sendAsync(build, BodyHandlers.ofString())
                    .thenAccept(response -> {
                        if (response.statusCode() == 200) {
                            MinerInfo minerInfo = null;
                            try {
                                minerInfo = objectMapper.readValue(response.body(), MinerInfo.class);
                            } catch (JsonProcessingException e) {
                                numberOfServersToCheck--;
                                throw new RuntimeException(e);
                            }
                            String mac = minerInfo.system.network_status.mac;
                            log.info("One more miner found: {}", mac);
                            miners.add(new Miner(mac, getMacAddress.miner.ipAddress));
                        } else {
                            log.error(STR."Failed to get mac address for \{getMacAddress.miner.ipAddress}");
                        }
                        numberOfServersToCheck--;

                        checkIfFinished();
                    })
                    .exceptionally(ex -> {
                        numberOfServersToCheck--;
                        log.error(STR."Failed to get mac address for \{getMacAddress.miner.ipAddress} \{ex.getMessage()}");
                        return null;
                    });
        }

        return this;
    }

    private void checkIfFinished() {
        self.tell(new Message.CheckScanFinished());
    }

    //{"miner":"Antminer S19J Pro","model":"s19jpro","fw_name":"Vnish","fw_version":"1.2.5-beta1","platform":"xil","install_type":"nand","build_time":"2024-03-01 00:47:15","hr_measure":"GH/s","system":{"os":"GNU/Linux","miner_name":"DAMx3A","file_system_version":"","mem_total":233712,"mem_free":191868,"mem_free_percent":82,"mem_buf":23556,"mem_buf_percent":10,"network_status":{"mac":"28:6C:5E:A9:BC:ED","dhcp":true,"ip":"192.168.110.54","netmask":"255.255.255.0","gateway":"192.168.110.1","dns":["192.168.110.1"],"hostname":"Antminer"},"uptime":"27 days, 12:24"}}
    @JsonIgnoreProperties(ignoreUnknown = true)
    record MinerInfo(
            String miner, String model, String fw_name, String fw_version, String platform,
            String install_type, String build_time, String hr_measure, System system) {
        @JsonIgnoreProperties(ignoreUnknown = true)
        record System(String os, String miner_name, String file_system_version, int mem_total, int mem_free,
                      int mem_free_percent, int mem_buf, int mem_buf_percent, NetworkStatus network_status,
                      String uptime) {
            @JsonIgnoreProperties(ignoreUnknown = true)
            record NetworkStatus(String mac, boolean dhcp, String ip, String netmask, String gateway, List<String> dns,
                                 String hostname) {
            }
        }
    }

    private Behavior<Message> onCheckScanFinished(Message.CheckScanFinished checkScanFinished) {
        log.info(STR."Log me Miners found so far \{miners.size()}");
        log.info(STR."Miners to check \{numberOfServersToCheck}");
        if (numberOfServersToCheck == 0) {
            minersController.tell(new MinersIps(miners.stream()
                    .map(miner -> new MinersController.Miner(miner.id, miner.ipAddress, 80))
                    .toList())
            );
            return Behaviors.stopped();
        }
        return this;
    }

    private Behavior<Message> onMinerReplied(Message.ServerReplied serverReplied) {
        if (!serverReplied.isOnline) {
            numberOfServersToCheck--;
            checkIfFinished();
            return this;
        }

        log.debug(STR."Server replied on ip: \{serverReplied.ipAddress}");
        final Miner miner = new Miner(null, serverReplied.ipAddress);

        try (HttpClient httpClient = HttpClient.newHttpClient()) {
            HttpRequest build = HttpRequest.newBuilder().GET()
                    .uri(URI.create(STR."http:/\{serverReplied.ipAddress}"))
                    .build();
            httpClient.sendAsync(build, BodyHandlers.ofString())
                    .thenAccept(response -> {
                        if (response.statusCode() == 200) {
                            if (response.body().contains("AnthillOS")) {
                                self.tell(new Message.GetMacAddress(miner, null));
                            }
                        } else {
                            numberOfServersToCheck--;
                            log.info(STR."Failed to get response from \{serverReplied.ipAddress} most likely not a miner");
                        }
                    })
                    .exceptionally(ex -> {
                        numberOfServersToCheck--;
                        log.error(STR."Failed to get response from \{serverReplied.ipAddress} \{ex.getMessage()}");
                        return null;
                    });
            return this;
        }
    }

    private Behavior<Message> onScanFromSubnet(Message.ScanFromSubnet scanFromSubnet) {
        try {
            String[] addrMask = scanFromSubnet.subnet.split("/");
            byte[] address = InetAddress.getByName(addrMask[0]).getAddress();
            int maskLength = Integer.parseInt(addrMask[1]);
            List<byte[]> addresses = getAllAddresses(
                    address,
                    maskLength,
                    true
            );
            log.info(STR."number of addresses to scan \{addresses.size()}");

            numberOfServersToCheck = addresses.size();
            for (byte[] addr : addresses) {
                InetAddress inetAddress = InetAddress.getByAddress(addr);
                CompletableFuture<Boolean> checkFuture = checkServerOnline(inetAddress, 80, 3000);

                getContext().pipeToSelf(checkFuture, (result, ex) -> {
                    if (ex == null) {
                        return new Message.ServerReplied(inetAddress, result);
                    } else {
                        log.error(STR."Failed to check server \{inetAddress}");
                        numberOfServersToCheck--;
                        throw new RuntimeException(ex);
                    }
                });

                log.debug(STR."Checking address \{inetAddress}");
            }
            return this;
        } catch (UnknownHostException e) {
            throw new RuntimeException(e);
        }
    }

    public CompletableFuture<Boolean> checkServerOnline(InetAddress inetAddress, int port, int timeout) {
        Logger log = getContext().getLog();
        return CompletableFuture.supplyAsync(() -> {
            boolean online = false;
            Socket socket = new Socket();
            try {
                socket.connect(new InetSocketAddress(inetAddress, port), timeout);
                online = true;
            } catch (SocketTimeoutException e) {
                log.debug("Connection timeout.");
            } catch (IOException e) {
                numberOfServersToCheck--;
                log.debug(STR."Error connecting to server: \{e.getMessage()}");
            } finally {
                try {
                    socket.close();
                } catch (IOException ex) {
                    log.error(STR."Error closing socket: \{ex.getMessage()}");
                }
            }
            return online;
        }, getContext().getSystem().executionContext());
    }

    private static List<byte[]> getAllAddresses(byte[] address, int maskLength, boolean scrub) {
        if (scrub) scrubAddress(address, maskLength);

        if (maskLength >= address.length * 8) return Collections.singletonList(address);

        int set = maskLength / 8;
        int pos = maskLength % 8;

        byte[] addressLeft = address.clone();
        addressLeft[set] |= (byte) (1 << pos);
        List<byte[]> addresses = new ArrayList<>(getAllAddresses(addressLeft, maskLength + 1, false));

        byte[] addressRight = address.clone();
        addressRight[set] &= (byte) ~(1 << pos);
        addresses.addAll(getAllAddresses(addressRight, maskLength + 1, false));

        return addresses;
    }

    private static void scrubAddress(byte[] address, int maskLength) {
        for (int i = 0; i < address.length * 8; i++) {
            if (i < maskLength) continue;

            address[i / 8] &= (byte) ~(1 << (i % 8));
        }

    }

    public interface Message {
        enum ReceiveTimeout implements Message {
            INSTANCE
        }

        public record ScanFromSubnet(String subnet) implements Message {
        }

        record ServerReplied(InetAddress ipAddress, Boolean isOnline) implements Message {
        }

        record CheckScanFinished() implements Message {

        }

        record MinerWeb(HttpResponse<String> r, Miner miner) implements Message {
        }

        record GetMacAddress(Miner miner, String token) implements Message {
        }
    }

    record Miner(String id, InetAddress ipAddress) {
    }
}
