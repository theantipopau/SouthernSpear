// Copyright Southern Spear. All Rights Reserved.

#include "SSKitSelection.h"

#include "GameFramework/Controller.h"

void USSKitSelection::RequestKit(AController* Controller, ESSKitRole Role)
{
	if (!Controller)
	{
		return;
	}
	Choices.Add(Controller, Role);
	Pending.Add(Controller);
}

bool USSKitSelection::GetKit(const AController* Controller, ESSKitRole& OutRole) const
{
	if (const ESSKitRole* Found = Choices.Find(Controller))
	{
		OutRole = *Found;
		return true;
	}
	return false;
}

bool USSKitSelection::ConsumeChange(const AController* Controller)
{
	return Pending.Remove(Controller) > 0;
}
