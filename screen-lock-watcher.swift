import Cocoa

let center = DistributedNotificationCenter.default()

center.addObserver(forName: NSNotification.Name("com.apple.screenIsLocked"), object: nil, queue: .main) { _ in
    let task = Process()
    task.launchPath = "/bin/bash"
    task.arguments = ["/Users/jing/Documents/pma/auto-git-sync.sh"]
    try? task.run()
    task.waitUntilExit()
}

RunLoop.main.run()
