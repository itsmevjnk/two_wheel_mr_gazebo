#include <optional>
#include <iostream>
#include <memory>

#include <stdlib.h>

#include "rclcpp/rclcpp.hpp"
#include "rclcpp/executors/single_threaded_executor.hpp"

/* domain_bridge */
#include "domain_bridge/domain_bridge.hpp"
#include "domain_bridge/component_manager.hpp"


int main(int argc, char **argv) {
    auto args = rclcpp::init_and_remove_ros_arguments(argc, argv);

    std::optional<size_t> from_domain;
    std::optional<size_t> to_domain;
    std::optional<std::string> nspace;
    /* parse arguments */
    for (auto it = ++args.cbegin(); it != args.cend(); ++it) {
        const auto &arg = *it;

        if (arg == "--from") {
            if (from_domain) {
                std::cerr << "ERROR: --from argument already provided" << std::endl;
                return -1;
            }
            ++it;
            if (it == args.cend()) {
                std::cerr << "ERROR: --from argument requires a value" << std::endl;
                return -1;
            }
            from_domain = std::stoul(*it);            
        } else if (arg == "--to") {
            if (to_domain) {
                std::cerr << "ERROR: --to argument already provided" << std::endl;
                return -1;
            }
            ++it;
            if (it == args.cend()) {
                std::cerr << "ERROR: --to argument requires a value" << std::endl;
                return -1;
            }
            to_domain = std::stoul(*it);
        } else if (arg == "--namespace") {
            if (nspace) {
                std::cerr << "ERROR: --namespace argument already provided" << std::endl;
                return -1;
            }
            ++it;
            if (it == args.cend()) {
                std::cerr << "ERROR: --namespace argument requires a value" << std::endl;
                return -1;
            }
            nspace = *it;
        } else {
            std::cerr << "ERROR: unknown argument: " << arg << std::endl;
            return -1;
        }
    }

    auto ros_domain_id = getenv("ROS_DOMAIN_ID"); if (!ros_domain_id) ros_domain_id = "0";
    auto from_domain_id = from_domain.value_or(atol(ros_domain_id));

    if (!to_domain) {
        std::cerr << "ERROR: --to argument is required" << std::endl;
        return -1;
    }
    auto to_domain_id = to_domain.value();

    if (!nspace) {
        std::cerr << "ERROR: --namespace argument is required" << std::endl;
        return -1;
    }
    auto robot_ns = nspace.value();

    std::cout << "Bridging topics and services (on namespace " << robot_ns << ") from domain " << from_domain_id << " to " << to_domain_id << std::endl;

    /* set up bridge config */
    domain_bridge::DomainBridgeConfig config;
    std::string topic_prefix = "/" + robot_ns;
    config.options.name(robot_ns + "_bridge");
    config.topics = {
        {domain_bridge::TopicBridge{"/clock", "rosgraph_msgs/msg/Clock", from_domain_id, to_domain_id}, domain_bridge::TopicBridgeOptions()},
        {domain_bridge::TopicBridge{"/cmd_vel", "geometry_msgs/msg/Twist", to_domain_id, from_domain_id}, domain_bridge::TopicBridgeOptions().remap_name(topic_prefix + "/cmd_vel").wait_for_publisher(false)}, // cmd_vel publisher comes after subscriber
        {domain_bridge::TopicBridge{topic_prefix + "/odom", "nav_msgs/msg/Odometry", from_domain_id, to_domain_id}, domain_bridge::TopicBridgeOptions().remap_name("/odom")},
        {domain_bridge::TopicBridge{topic_prefix + "/scan", "sensor_msgs/msg/LaserScan", from_domain_id, to_domain_id}, domain_bridge::TopicBridgeOptions().remap_name("/scan")},
    };

    domain_bridge::DomainBridge bridge(config);
    
    auto executor = std::make_shared<rclcpp::executors::SingleThreadedExecutor>();
    auto node = std::make_shared<domain_bridge::ComponentManager>(executor);

    bridge.add_to_executor(*executor);
    executor->add_node(node);
    executor->spin();

    rclcpp::shutdown();
    return 0;
}