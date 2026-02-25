import pexpect
import sys

def ssh_esxi():
    try:
        # Start SSH session
        child = pexpect.spawn('ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 root@10.0.1.136')
        
        # Wait for password prompt
        index = child.expect(['Password:', pexpect.EOF, pexpect.TIMEOUT], timeout=15)
        
        if index == 0:
            # Send password
            child.sendline('www199054@')
        elif index == 1:
            print("EOF received before password prompt (Connection closed?)")
            print(child.before.decode())
            return
        elif index == 2:
            print("Timeout waiting for password prompt")
            return

        # Wait for shell prompt or failure
        # ESXi shell prompt usually ends with # or >
        # Or error message "Permission denied"
        index = child.expect(['#', 'Permission denied', 'Access denied', pexpect.EOF, pexpect.TIMEOUT], timeout=15)
        
        if index == 0:
            print("Login successful!")
            # Get current time
            child.sendline('esxcli system time get')
            child.expect('#')
            print("Current Time:", child.before.decode().strip())
            
            # Check NTP
            child.sendline('esxcli system ntp get')
            child.expect('#')
            print("NTP Status:", child.before.decode().strip())
            
            # Fix time: Enable NTP
            child.sendline('esxcli system ntp set --enabled=true')
            child.expect('#')
            child.sendline('esxcli network firewall ruleset set --enabled=true --ruleset-id=ntpClient')
            child.expect('#')
            
            # Check again
            child.sendline('esxcli system ntp get')
            child.expect('#')
            print("NTP Status after fix:", child.before.decode().strip())
            
            child.sendline('exit')
        elif index == 1 or index == 2:
            print("Login failed: Permission denied / Access denied")
            print(child.before.decode())
        else:
            print("Failed to get shell prompt")
            print(child.before.decode())
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ssh_esxi()
