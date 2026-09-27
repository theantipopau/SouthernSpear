// Copyright Southern Spear. All Rights Reserved.

#include "SSMenuWidget.h"

#include "Components/BackgroundBlur.h"
#include "Components/ScaleBox.h"
#include "Engine/Texture2D.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "SSSettingsWidget.h"
#include "SSUIAssets.h"
#include "SSWidgetKit.h"

using namespace SSWidgetKit;

const TCHAR* USSMenuWidget::FrontEndMap = TEXT("/Game/Maps/L_SS_FrontEnd");
int32 USSMenuWidget::SelectedBots = 8;

namespace
{
	constexpr float PanelWidth = 470.f;

	FSlateBrush Flat(const FLinearColor& C)
	{
		FSlateBrush Brush;
		Brush.DrawAs = ESlateBrushDrawType::Box;
		Brush.TintColor = FSlateColor(C);
		return Brush;
	}

	void StyleButton(UButton* Button, const FLinearColor& Normal, const FLinearColor& Hover, const FMargin& Padding)
	{
		FButtonStyle Style = Button->GetStyle();
		Style.SetNormal(Flat(Normal));
		Style.SetHovered(Flat(Hover));
		Style.SetPressed(Flat(SSPalette::Brass300()));
		Style.SetNormalPadding(Padding);
		Style.SetPressedPadding(Padding);
		Button->SetStyle(Style);
	}

	UWidget* KeyArt(UWidgetTree* T)
	{
		UImage* Art = T->ConstructWidget<UImage>();
		if (UTexture2D* Texture = SSUIAssets::MainMenuArt())
		{
			Art->SetBrushFromTexture(Texture, /*bMatchSize=*/ true);
		}
		UScaleBox* Scale = T->ConstructWidget<UScaleBox>();
		Scale->SetStretch(EStretch::ScaleToFill);
		Scale->AddChild(Art);
		return Scale;
	}

	/** Map card: brass edge, title with a chevron, one-line description, meta line. */
	UButton* MapCard(UWidgetTree* T, const FText& Title, const FText& Description, const FText& Meta)
	{
		UButton* Button = T->ConstructWidget<UButton>();
		StyleButton(Button, SSPalette::Field800(0.9f), SSPalette::Field700(0.98f), FMargin(0.f));
		UHorizontalBox* Row = T->ConstructWidget<UHorizontalBox>();
		Button->AddChild(Row);
		USizeBox* Edge = T->ConstructWidget<USizeBox>();
		Edge->SetWidthOverride(4.f);
		Edge->AddChild(Plate(T, SSPalette::Brass500(), FMargin(0.f)));
		AddH(Row, Edge, false, VAlign_Fill);
		USizeBox* Width = T->ConstructWidget<USizeBox>();
		Width->SetWidthOverride(460.f);
		AddH(Row, Width)->SetPadding(FMargin(16.f, 8.f, 16.f, 10.f));
		UVerticalBox* Body = T->ConstructWidget<UVerticalBox>();
		Width->AddChild(Body);
		UHorizontalBox* Head = T->ConstructWidget<UHorizontalBox>();
		AddV(Body, Head);
		UTextBlock* TitleText = Text(T, 17, true, SSPalette::Sand100(), 100);
		TitleText->SetText(Title);
		AddH(Head, TitleText, true);
		UTextBlock* Go = Text(T, 16, true, SSPalette::Brass300());
		Go->SetText(FText::FromString(TEXT("›")));
		AddH(Head, Go);
		UTextBlock* DescText = Text(T, 12, false, SSPalette::Sage200());
		DescText->SetText(Description);
		DescText->SetAutoWrapText(true);
		AddV(Body, DescText, 4.f);
		UTextBlock* MetaText = Text(T, 10, true, SSPalette::Brass300(), 220);
		MetaText->SetText(Meta);
		AddV(Body, MetaText, 8.f);
		return Button;
	}

	/** Small caption with a short brass rule, as on the website section heads. */
	UWidget* Caption(UWidgetTree* T, const FText& Label)
	{
		UHorizontalBox* Row = T->ConstructWidget<UHorizontalBox>();
		AddH(Row, Rule(T, SSPalette::Brass500(), 2.f, 22.f));
		UTextBlock* CaptionText = Text(T, 11, true, SSPalette::Brass300(), 300);
		CaptionText->SetText(Label);
		AddH(Row, CaptionText)->SetPadding(FMargin(10.f, 0.f, 0.f, 0.f));
		return Row;
	}
}

UButton* USSMenuWidget::AddHandler(UButton* Button, FName Handler)
{
	FScriptDelegate Delegate;
	Delegate.BindUFunction(this, Handler);
	Button->OnClicked.Add(Delegate);
	return Button;
}

void USSMenuWidget::Setup(ESSMenuMode InMode)
{
	Mode = InMode;
	if (!WidgetTree || WidgetTree->RootWidget)
	{
		return;
	}
	UWidgetTree* T = WidgetTree;
	UCanvasPanel* Root = T->ConstructWidget<UCanvasPanel>();
	T->RootWidget = Root;
	UVerticalBox* Col = T->ConstructWidget<UVerticalBox>();
	Content = Col;

	if (Mode == ESSMenuMode::FrontEnd)
	{
		Fill(Root, KeyArt(T));
		// Left shade in three steps, so the art fades into the menu side.
		const float Widths[] = { 780.f, 660.f, 580.f };
		const float Alphas[] = { 0.25f, 0.35f, 0.55f };
		for (int32 Index = 0; Index < 3; ++Index)
		{
			UCanvasPanelSlot* ShadeSlot = Root->AddChildToCanvas(Plate(T, SSPalette::Ink950(Alphas[Index]), FMargin(0.f)));
			ShadeSlot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 1.f));
			ShadeSlot->SetOffsets(FMargin(0.f, 0.f, Widths[Index], 0.f));
		}

		// Top bar: wordmark left, status right.
		UBorder* TopBar = Plate(T, SSPalette::Ink950(0.7f), FMargin(72.f, 14.f));
		UCanvasPanelSlot* TopSlot = Root->AddChildToCanvas(TopBar);
		TopSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 0.f));
		TopSlot->SetOffsets(FMargin(0.f, 0.f, 0.f, 48.f));
		UHorizontalBox* TopRow = T->ConstructWidget<UHorizontalBox>();
		TopBar->SetContent(TopRow);
		UTextBlock* Mark = Text(T, 13, true, SSPalette::Sand100(), 400);
		Mark->SetText(NSLOCTEXT("SSMenu", "Mark", "SOUTHERN SPEAR"));
		AddH(TopRow, Mark);
		AddH(TopRow, T->ConstructWidget<USpacer>(), true);
		UTextBlock* Status = Text(T, 11, true, SSPalette::Brass300(), 300);
		Status->SetText(NSLOCTEXT("SSMenu", "Status", "PRE-ALPHA  ·  OFFLINE WITH BOTS"));
		AddH(TopRow, Status);
		UCanvasPanelSlot* TopRuleSlot = Root->AddChildToCanvas(Rule(T, SSPalette::Brass500(0.8f), 1.f));
		TopRuleSlot->SetAnchors(FAnchors(0.f, 0.f, 1.f, 0.f));
		TopRuleSlot->SetOffsets(FMargin(0.f, 48.f, 0.f, 1.f));

		Pin(Root, Col, FVector2D(0.f, 0.5f), FVector2D(72.f, 12.f));

		UTextBlock* Kicker = Text(T, 12, true, SSPalette::Brass300(), 300);
		Kicker->SetText(NSLOCTEXT("SSMenu", "Kicker", "TACTICAL FIRST-PERSON SHOOTER"));
		AddV(Col, Stagger(Kicker));
		TitleText = Text(T, 52, true, SSPalette::Sand100(), 100);
		TitleText->SetText(NSLOCTEXT("SSMenu", "Title", "SOUTHERN SPEAR"));
		AddV(Col, Stagger(TitleText), 2.f);
		AddV(Col, Stagger(Rule(T, SSPalette::Brass500(), 2.f, 120.f)), 10.f, HAlign_Left);

		AddV(Col, Stagger(Caption(T, NSLOCTEXT("SSMenu", "Deploy", "DEPLOY  ·  OBJECTIVE ASSAULT"))), 22.f);
		AddV(Col, Stagger(AddHandler(MapCard(T, NSLOCTEXT("SSMenu", "RedGum", "RED GUM STATION"),
			NSLOCTEXT("SSMenu", "RedGumDesc", "An outback cattle station. Take the bore pump, the homestead and the shearing shed in order."),
			NSLOCTEXT("SSMenu", "RedGumMeta", "3 OBJECTIVES  ·  OPEN PADDOCKS  ·  LONG SIGHTLINES")),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnRedGum))), 12.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MapCard(T, NSLOCTEXT("SSMenu", "DryRiver", "DRY RIVER"),
			NSLOCTEXT("SSMenu", "DryRiverDesc", "A dry creek line between a water point and a farmstead."),
			NSLOCTEXT("SSMenu", "DryRiverMeta", "2 OBJECTIVES  ·  CREEK BED  ·  FARMSTEAD")),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnDryRiver))), 6.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MapCard(T, NSLOCTEXT("SSMenu", "Saltbush", "SALTBUSH FLATS"),
			NSLOCTEXT("SSMenu", "SaltbushDesc", "Arid scrub and stone country. A windmill, the stock yards and a dry dam."),
			NSLOCTEXT("SSMenu", "SaltbushMeta", "3 OBJECTIVES  ·  COMPACT  ·  ROCKY COVER")),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnSaltbush))), 6.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MapCard(T, NSLOCTEXT("SSMenu", "SelatCanal", "SELAT CANAL"),
			NSLOCTEXT("SSMenu", "SelatCanalDesc", "A Murasian canal district. Fight over the footbridge, market row and pump house."),
			NSLOCTEXT("SSMenu", "SelatCanalMeta", "3 OBJECTIVES  ·  URBAN  ·  CLOSE QUARTERS")),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnSelatCanal))), 6.f, HAlign_Left);

		// Bots: 4 / 8 / 12.
		AddV(Col, Stagger(Caption(T, NSLOCTEXT("SSMenu", "Bots", "BOTS PER MATCH"))), 24.f);
		UHorizontalBox* BotRow = T->ConstructWidget<UHorizontalBox>();
		AddV(Col, Stagger(BotRow), 10.f, HAlign_Left);
		const TPair<int32, FName> Choices[] = {
			{ 4, GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnBots4) },
			{ 8, GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnBots8) },
			{ 12, GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnBots12) } };
		for (const TPair<int32, FName>& Choice : Choices)
		{
			UButton* Button = T->ConstructWidget<UButton>();
			USizeBox* Size = T->ConstructWidget<USizeBox>();
			Size->SetWidthOverride(52.f);
			UTextBlock* Label = Text(T, 14, true, SSPalette::Sand100());
			Label->SetText(FText::AsNumber(Choice.Key));
			Label->SetJustification(ETextJustify::Center);
			Size->AddChild(Label);
			Button->AddChild(Size);
			AddH(BotRow, AddHandler(Button, Choice.Value))->SetPadding(FMargin(0.f, 0.f, 6.f, 0.f));
			BotButtons.Add(Button);
		}
		SetBots(SelectedBots);

		UHorizontalBox* Bottom = T->ConstructWidget<UHorizontalBox>();
		AddV(Col, Stagger(Bottom), 32.f, HAlign_Left);
		AddH(Bottom, AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "Settings", "SETTINGS"), 170.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnSettings)))->SetPadding(FMargin(0.f, 0.f, 10.f, 0.f));
		AddH(Bottom, AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "Quit", "QUIT"), 170.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnQuit)));

		UTextBlock* Footer = Text(T, 11, false, SSPalette::Sage400(), 60);
		Footer->SetText(NSLOCTEXT("SSMenu", "Footer", "A fictional setting. Not affiliated with any real defence force."));
		Pin(Root, Stagger(Footer), FVector2D(0.f, 1.f), FVector2D(72.f, -28.f));
		UTextBlock* Keys = Text(T, 11, true, SSPalette::Sage400(), 200);
		Keys->SetText(NSLOCTEXT("SSMenu", "Keys", "WASD MOVE  ·  RMB AIM  ·  R RELOAD  ·  M MAP  ·  ESC MENU"));
		Pin(Root, Stagger(Keys), FVector2D(1.f, 1.f), FVector2D(-72.f, -28.f));

		// Intro: the whole screen rises out of black.
		Curtain = Plate(T, SSPalette::Ink950(), FMargin(0.f));
		Curtain->SetVisibility(ESlateVisibility::HitTestInvisible);
		Fill(Root, Curtain);
	}
	else
	{
		UBackgroundBlur* Blur = T->ConstructWidget<UBackgroundBlur>();
		Blur->SetBlurStrength(6.f);
		Fill(Root, Blur);
		Fill(Root, Plate(T, SSPalette::Ink950(0.45f), FMargin(0.f)));

		// Side panel, full height, sliding in from the left.
		UBorder* Side = Plate(T, SSPalette::Ink900(0.94f), FMargin(56.f, 0.f, 40.f, 0.f));
		SidePanel = Side;
		UCanvasPanelSlot* SideSlot = Root->AddChildToCanvas(Side);
		SideSlot->SetAnchors(FAnchors(0.f, 0.f, 0.f, 1.f));
		SideSlot->SetOffsets(FMargin(0.f, 0.f, PanelWidth, 0.f));
		Side->SetVerticalAlignment(VAlign_Center);
		Side->SetContent(Col);

		UTextBlock* Kicker = Text(T, 11, true, SSPalette::Brass300(), 300);
		Kicker->SetText(NSLOCTEXT("SSMenu", "Paused", "THE MATCH CONTINUES"));
		AddV(Col, Stagger(Kicker));
		UTextBlock* Title = Text(T, 38, true, SSPalette::Sand100(), 100);
		Title->SetText(NSLOCTEXT("SSMenu", "MatchMenu", "MATCH MENU"));
		AddV(Col, Stagger(Title), 2.f);
		AddV(Col, Stagger(Rule(T, SSPalette::Brass500(), 2.f, 96.f)), 10.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "Resume", "RESUME"), 360.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnResume))), 28.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "Settings", "SETTINGS"), 360.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnSettings))), 8.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "MainMenu", "LEAVE MATCH"), 360.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnMainMenu))), 8.f, HAlign_Left);
		AddV(Col, Stagger(AddHandler(MenuButton(T, NSLOCTEXT("SSMenu", "QuitGame", "QUIT TO DESKTOP"), 360.f),
			GET_FUNCTION_NAME_CHECKED(USSMenuWidget, OnQuit))), 8.f, HAlign_Left);

		// Controls card, bottom right.
		UVerticalBox* Card = T->ConstructWidget<UVerticalBox>();
		Pin(Root, Stagger(Card), FVector2D(1.f, 1.f), FVector2D(-48.f, -48.f));
		AddV(Card, Rule(T, SSPalette::Brass500(), 2.f, 300.f));
		UBorder* CardPlate = Plate(T, SSPalette::Ink900(0.9f), FMargin(18.f, 12.f, 18.f, 14.f));
		AddV(Card, CardPlate);
		UVerticalBox* CardBody = T->ConstructWidget<UVerticalBox>();
		CardPlate->SetContent(CardBody);
		AddV(CardBody, Caption(T, NSLOCTEXT("SSMenu", "Controls", "CONTROLS")));
		const TPair<const TCHAR*, FText> Bindings[] = {
			{ TEXT("WASD"), NSLOCTEXT("SSMenu", "Move", "Move") },
			{ TEXT("LMB"), NSLOCTEXT("SSMenu", "Fire", "Fire") },
			{ TEXT("RMB"), NSLOCTEXT("SSMenu", "Aim", "Aim down sights") },
			{ TEXT("R"), NSLOCTEXT("SSMenu", "ReloadKey", "Reload") },
			{ TEXT("M"), NSLOCTEXT("SSMenu", "MapKey", "Full map") },
			{ TEXT("ESC"), NSLOCTEXT("SSMenu", "MenuKey", "This menu") } };
		for (const TPair<const TCHAR*, FText>& Binding : Bindings)
		{
			UHorizontalBox* Line = T->ConstructWidget<UHorizontalBox>();
			AddV(CardBody, Line, 6.f);
			USizeBox* KeySize = T->ConstructWidget<USizeBox>();
			KeySize->SetWidthOverride(64.f);
			UTextBlock* Key = Text(T, 12, true, SSPalette::Sand100(), 120);
			Key->SetText(FText::FromString(Binding.Key));
			KeySize->AddChild(Key);
			AddH(Line, KeySize);
			UTextBlock* Action = Text(T, 12, false, SSPalette::Sage200());
			Action->SetText(Binding.Value);
			AddH(Line, Action);
		}
	}
}

void USSMenuWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	Elapsed += InDeltaTime;

	if (Curtain)
	{
		const float Fade = Ease(Elapsed, 0.15f, 0.9f);
		Curtain->SetRenderOpacity(1.f - Fade);
		Curtain->SetVisibility(Fade >= 1.f ? ESlateVisibility::Collapsed : ESlateVisibility::HitTestInvisible);
	}
	if (TitleText)
	{
		// The title tightens from wide tracking into place.
		FSlateFontInfo Font = TitleText->GetFont();
		Font.LetterSpacing = FMath::RoundToInt(FMath::Lerp(420.f, 100.f, Ease(Elapsed, 0.2f, 1.1f)));
		TitleText->SetFont(Font);
	}
	if (SidePanel)
	{
		const float Slide = Ease(Elapsed, 0.f, 0.28f);
		SidePanel->SetRenderTranslation(FVector2D((1.f - Slide) * -PanelWidth, 0.f));
	}
	const float Start = Mode == ESSMenuMode::FrontEnd ? 0.35f : 0.1f;
	for (int32 Index = 0; Index < Animated.Num(); ++Index)
	{
		Reveal(Animated[Index], Ease(Elapsed, Start + 0.05f * Index, 0.35f));
	}
}

void USSMenuWidget::SetBots(int32 Count)
{
	SelectedBots = Count;
	const int32 Values[] = { 4, 8, 12 };
	for (int32 Index = 0; Index < BotButtons.Num(); ++Index)
	{
		const bool bOn = Values[Index] == Count;
		StyleButton(BotButtons[Index], bOn ? SSPalette::Brass500(0.95f) : SSPalette::Field800(0.9f),
			bOn ? SSPalette::Brass300() : SSPalette::Field700(0.98f), FMargin(8.f, 8.f));
	}
}

void USSMenuWidget::PlayMap(const UObject* Context, const TCHAR* Map)
{
	if (APlayerController* Player = UGameplayStatics::GetPlayerController(Context, 0))
	{
		Player->SetInputMode(FInputModeGameOnly());
		Player->SetShowMouseCursor(false);
	}
	UGameplayStatics::OpenLevel(Context, FName(Map), /*bAbsolute=*/ true, FString::Printf(TEXT("NumBots=%d"), SelectedBots));
}

void USSMenuWidget::OnRedGum()   { PlayMap(this, TEXT("/Game/Maps/L_RedGum_01")); }
void USSMenuWidget::OnDryRiver() { PlayMap(this, TEXT("/Game/Maps/L_DryRiver_01")); }
void USSMenuWidget::OnSaltbush()  { PlayMap(this, TEXT("/Game/Maps/L_Saltbush_01")); }
void USSMenuWidget::OnSelatCanal() { PlayMap(this, TEXT("/Game/Maps/L_SelatCanal_01")); }
void USSMenuWidget::OnBots4()    { SetBots(4); }
void USSMenuWidget::OnBots8()    { SetBots(8); }
void USSMenuWidget::OnBots12()   { SetBots(12); }

void USSMenuWidget::OnSettings()
{
	if (!Settings)
	{
		Settings = CreateWidget<USSSettingsWidget>(GetOwningPlayer(), USSSettingsWidget::StaticClass());
		if (!Settings)
		{
			return;
		}
		Settings->AddToViewport(70);
		TWeakObjectPtr<USSMenuWidget> WeakThis(this);
		Settings->OnClosed = [WeakThis]()
		{
			if (USSMenuWidget* Menu = WeakThis.Get())
			{
				Menu->Content->SetVisibility(ESlateVisibility::Visible);
				Menu->Replay();
			}
		};
	}
	Settings->SetVisibility(ESlateVisibility::Visible);
	Settings->Replay();
	Content->SetVisibility(ESlateVisibility::Hidden);
}

void USSMenuWidget::OnResume()
{
	if (APlayerController* Player = GetOwningPlayer())
	{
		Player->SetInputMode(FInputModeGameOnly());
		Player->SetShowMouseCursor(false);
	}
	if (Settings)
	{
		Settings->SetVisibility(ESlateVisibility::Collapsed);
	}
	SetVisibility(ESlateVisibility::Collapsed);
}

void USSMenuWidget::OnMainMenu()
{
	UGameplayStatics::OpenLevel(this, FName(FrontEndMap), /*bAbsolute=*/ true);
}

void USSMenuWidget::OnQuit()
{
	UKismetSystemLibrary::QuitGame(this, GetOwningPlayer(), EQuitPreference::Quit, false);
}
